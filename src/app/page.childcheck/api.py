import json
import re
import datetime
import hashlib

Users = wiz.model("db/login_db/users")
Children = wiz.model("db/childcheck/children")
ChildAllergies = wiz.model("db/childcheck/child_allergies")
Meals = wiz.model("db/childcheck/meals")
ServerMembers = wiz.model("db/login_db/server_members")

# 19종 알레르기 타입명 매핑 (view.ts에서 보내는 이름 → DB 저장용)
_STANDARD_ALLERGY_NAMES = [
    '난류', '우유', '메밀', '땅콩', '대두', '밀', '고등어', '게', '새우',
    '돼지고기', '복숭아', '토마토', '아황산류', '호두', '닭고기', '소고기',
    '오징어', '조개류', '잣'
]

def get_child_info():
    user_id = wiz.session.get("id")
    if not user_id:
        wiz.response.status(401, message="로그인이 필요합니다.")

    try:
        child = Children.select().where(Children.user_id == user_id).first()
    except Exception as e:
        wiz.response.status(500, message="DB 조회 오류: " + str(e))

    if not child:
        # 기존 users 테이블에서 이름/생일 정보 보조로 가져옴
        try:
            user = Users.select().where(Users.id == user_id).first()
        except Exception:
            user = None
        wiz.response.status(200,
            child_name=(user.child_name if user and user.child_name else ''),
            birth_date=(str(user.birth_date) if user and user.birth_date else ''),
            twin_type='없음',
            allergies=[],
            is_severe=False,
            needs_substitute=False
        )

    # 기존 알레르기 로드
    try:
        allergy_rows = list(ChildAllergies.select().where(ChildAllergies.child_id == child.id).dicts())
    except Exception:
        allergy_rows = []

    allergies = []
    is_severe = False
    needs_substitute = False
    for row in allergy_rows:
        allergies.append({
            "allergy_type": row.get("allergy_type", ""),
            "other_detail": row.get("other_detail", "")
        })
        if row.get("is_severe"):
            is_severe = True
        if row.get("needs_substitute"):
            needs_substitute = True

    wiz.response.status(200,
        child_name=child.name or '',
        birth_date=str(child.birthdate) if child.birthdate else '',
        twin_type=child.twin_type or '없음',
        allergies=allergies,
        is_severe=is_severe,
        needs_substitute=needs_substitute
    )

def save_childcheck():
    user_id = wiz.session.get("id")
    if not user_id:
        wiz.response.status(401, message="로그인이 필요합니다.")

    child_name = wiz.request.query("child_name", True)
    birth_date = wiz.request.query("birth_date", "")
    twin_type = wiz.request.query("twin_type", "없음")
    allergies_json = wiz.request.query("allergies", "[]")
    is_severe = wiz.request.query("is_severe", "false") == "true"
    needs_substitute = wiz.request.query("needs_substitute", "false") == "true"

    try:
        allergies = json.loads(allergies_json)
    except Exception:
        allergies = []

    # children 테이블에 upsert
    try:
        child = Children.select().where(Children.user_id == user_id).first()
        if child:
            # 기존 아이 정보 업데이트
            Children.update(
                name=child_name,
                birthdate=birth_date if birth_date else None,
                twin_type=twin_type,
                allergy_checked=True
            ).where(Children.user_id == user_id).execute()
            child_id = child.id
        else:
            # 신규 생성
            child = Children.create(
                user_id=user_id,
                name=child_name,
                birthdate=birth_date if birth_date else None,
                twin_type=twin_type,
                allergy_checked=True
            )
            child_id = child.id
    except Exception as e:
        wiz.response.status(500, message="자녀 정보 저장 오류: " + str(e))

    # child_allergies: 기존 삭제 후 재삽입
    try:
        ChildAllergies.delete().where(ChildAllergies.child_id == child_id).execute()
    except Exception:
        pass
    for allergy in allergies:
        allergy_type = allergy.get("allergy_type", "")
        other_detail = allergy.get("other_detail", "")
        try:
            ChildAllergies.create(
                child_id=child_id,
                allergy_type=allergy_type,
                other_detail=other_detail,
                is_severe=is_severe,
                needs_substitute=needs_substitute
            )
        except Exception as e:
            print("[CHILDCHECK] 알레르기 저장 오류:", str(e))

    # 기타 알레르기가 있으면 → 이번 달 식단과 AI 배치 매칭하여 캐시 생성
    other_details = [a.get('other_detail', '').strip() for a in allergies if a.get('allergy_type') == '기타' and a.get('other_detail', '').strip()]
    if other_details:
        try:
            _build_ingredient_allergy_cache(user_id, other_details)
        except Exception as e:
            print(f"[CHILDCHECK] 기타 알레르기 캐시 생성 실패: {e}")

    wiz.response.status(200, hasCompletedAllergyCheck=True)


def _build_ingredient_allergy_cache(user_id, other_keywords):
    """기타 알레르기 키워드로 이번 달 식단 전체 음식을 AI 배치 분석하여 캐시 저장.
    결과: data/allergy_ingredient_cache/{server_id}/{month}/{keyword_hash}.json
    """
    server_id = wiz.session.get("server_id") or wiz.session.get("join_server_id")
    if not server_id:
        return

    today = datetime.date.today()
    month_str = today.strftime("%Y-%m")
    first_day = today.replace(day=1)
    if today.month == 12:
        last_day = today.replace(year=today.year + 1, month=1, day=1) - datetime.timedelta(days=1)
    else:
        last_day = today.replace(month=today.month + 1, day=1) - datetime.timedelta(days=1)

    # 이번 달 식단에서 모든 음식명 추출
    try:
        meals = list(Meals.select(Meals.content).where(
            (Meals.server_id == int(server_id)) &
            (Meals.date >= first_day) &
            (Meals.date <= last_day)
        ))
    except Exception:
        return

    all_dishes = set()
    for meal in meals:
        content = meal.content or ''
        # green 마커 처리
        content = re.sub(r'\{\{green:(.*?)\}\}', r'\1', content)
        for line in content.split('\n'):
            for item in re.split(r'[,/]', line):
                dish = re.sub(r'[\u2460-\u2473\u3251-\u325f\d.]+$', '', item).strip()
                dish = re.sub(r'[①-⑲⑳]+', '', dish).strip()
                if dish and len(dish) >= 2:
                    all_dishes.add(dish)

    if not all_dishes:
        return

    dishes_list = sorted(all_dishes)
    cache_fs = wiz.project.fs("data", "allergy_ingredient_cache", str(server_id), month_str)

    for keyword in other_keywords:
        kw_parts = [k.strip() for k in keyword.replace('/', ',').split(',') if k.strip()]
        for kw in kw_parts:
            cache_file = hashlib.md5(kw.encode()).hexdigest() + ".json"
            # 이미 캐시가 있으면 스킵
            try:
                if cache_fs.exists(cache_file):
                    continue
            except Exception:
                pass

            # AI에게 배치 분석 요청
            try:
                gemini = wiz.model("gemini")
                prompt = f"""다음은 어린이집 식단 음식 목록입니다:
{chr(10).join(dishes_list)}

이 음식들 중에서 "{kw}"이(가) 주재료 또는 부재료로 들어갈 가능성이 높은 음식을 모두 찾아주세요.
음식 이름에 "{kw}"이 직접 포함된 것뿐만 아니라, 조리과정에서 "{kw}"이 들어가는 음식도 포함해주세요.

JSON 형식으로 응답: {{"matched_dishes": ["음식1", "음식2", ...]}}
해당 음식이 없으면: {{"matched_dishes": []}}"""

                result = gemini.ask_json(prompt, system_instruction="식품 영양 전문가입니다. JSON만 응답하세요.")
                if isinstance(result, dict) and 'matched_dishes' in result:
                    matched = [d for d in result['matched_dishes'] if isinstance(d, str)]
                    cache_fs.write.json(cache_file, {"keyword": kw, "matched_dishes": matched, "all_dishes_count": len(dishes_list), "created": today.isoformat()})
            except Exception as e:
                print(f"[CHILDCHECK] AI 재료 매칭 실패 ({kw}): {e}")
