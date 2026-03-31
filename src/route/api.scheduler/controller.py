import json
import datetime
import os
import re

Meals = wiz.model("db/childcheck/meals")
Children = wiz.model("db/childcheck/children")
ChildAllergies = wiz.model("db/childcheck/child_allergies")
Notifications = wiz.model("db/childcheck/notifications")
AllergyCategories = wiz.model("db/childcheck/allergy_categories")
ServerMembers = wiz.model("db/login_db/server_members")
Users = wiz.model("db/login_db/users")
push = wiz.model("push")

SCHEDULER_KEY = "childnote-scheduler-2026"
KST = datetime.timezone(datetime.timedelta(hours=9))

# 알레르기 번호 → 한글명
ALLERGY_MAP = {
    1: '난류(계란)', 2: '우유', 3: '메밀', 4: '땅콩', 5: '대두',
    6: '밀', 7: '고등어', 8: '게', 9: '새우', 10: '돼지고기',
    11: '복숭아', 12: '토마토', 13: '아황산류', 14: '호두',
    15: '닭고기', 16: '소고기', 17: '오징어', 18: '조개류', 19: '잣'
}

# child_allergies.allergy_type (한글) → 알레르기 번호
ALLERGY_TYPE_TO_NUMBERS = {
    '계란': [1], '난류': [1], '우유': [2], '메밀': [3], '땅콩': [4],
    '대두': [5], '밀': [6], '고등어': [7], '게': [8], '새우': [9],
    '돼지고기': [10], '복숭아': [11], '토마토': [12], '아황산류': [13],
    '호두': [14], '닭고기': [15], '소고기': [16], '쇠고기': [16],
    '오징어': [17], '조개류': [18], '잣': [19]
}

KEYWORD_ALIASES = {
    '돼지고기': ['돼지'],
    '닭고기': ['닭'],
    '쇠고기': ['소고기', '쇠'],
    '소고기': ['쇠고기', '쇠'],
}

def _build_allergy_food_map():
    """AllergyCategories DB에서 알레르기 번호 → 주의식품 키워드 매핑 생성"""
    num_to_foods = {}
    try:
        for cat in AllergyCategories.select():
            try:
                numbers = json.loads(cat.allergy_numbers) if cat.allergy_numbers else []
            except Exception:
                numbers = []
            raw_foods = (cat.caution_foods or '').replace('(', ',').replace(')', ',')
            foods = [f.strip() for f in raw_foods.split(',') if f.strip()]
            for num in numbers:
                if num not in num_to_foods:
                    num_to_foods[num] = []
                num_to_foods[num].extend(foods)
    except Exception:
        pass
    return num_to_foods

def _find_dish_names(all_content, allergy_nums, num_to_foods):
    """식단 content에서 알레르기 해당 음식명 추출"""
    dishes = [d.strip() for d in re.split(r'[,\n/]', all_content) if d.strip()]
    dishes = [re.sub(r'[\u2460-\u2473\u3251-\u325f\d.]+$', '', d).strip() for d in dishes]
    dishes = [d for d in dishes if d]

    result = {}
    for num in allergy_nums:
        allergy_name = ALLERGY_MAP.get(num, str(num))
        keywords = num_to_foods.get(num, [])
        matched = []
        for dish in dishes:
            for kw in keywords:
                if kw in dish:
                    if dish not in matched:
                        matched.append(dish)
                    break
                for alias in KEYWORD_ALIASES.get(kw, []):
                    if alias in dish:
                        if dish not in matched:
                            matched.append(dish)
                        break
        result[allergy_name] = matched
    return result

def _get_staff_ids(server_id):
    """서버의 원장+교사 user_id 목록"""
    rows = ServerMembers.select(ServerMembers.user_id).where(
        (ServerMembers.server_id == server_id) &
        (ServerMembers.role.in_(["director", "teacher"]))
    )
    return [r.user_id for r in rows]

def _notify_user(user_id, noti_type, title, body):
    """인앱 알림 + 푸시 알림 전송"""
    try:
        Notifications.create(
            user_id=str(user_id),
            type=noti_type,
            title=title,
            message=body,
            link="/note"
        )
    except Exception as e:
        print(f"[SCHEDULER] 인앱 알림 오류 (user_id={user_id}): {e}")
    try:
        push.send_to_user(user_id, title, body, url="/note", noti_type=noti_type)
    except Exception as e:
        print(f"[SCHEDULER] 푸시 알림 오류 (user_id={user_id}): {e}")

def _notify_allergy_matches(server_id, matched_children):
    """알레르기 매칭된 아이의 부모 + 교직원에게 알림 (식단명 포함)"""
    # 부모별 알림
    for mc in matched_children:
        child = mc["child"]
        dish_details = mc.get("dish_details", {})
        detail_parts = []
        for aname, dishes in dish_details.items():
            if dishes:
                detail_parts.append(f"{', '.join(dishes)}({aname})")
            else:
                detail_parts.append(aname)
        detail_text = ", ".join(detail_parts) if detail_parts else ", ".join(mc["allergy_names"])
        title = "⚠️ 알레르기 식단 주의"
        body = f"오늘 식단에 {child.name}의 알레르기 식품이 포함되어 있습니다: {detail_text}"
        _notify_user(mc["parent_user_id"], "allergy_alert", title, body)

    # 교직원 요약 알림
    staff_ids = _get_staff_ids(server_id)
    child_parts = []
    for mc in matched_children:
        dish_details = mc.get("dish_details", {})
        detail_parts = []
        for aname, dishes in dish_details.items():
            if dishes:
                detail_parts.append(f"{', '.join(dishes)}({aname})")
            else:
                detail_parts.append(aname)
        detail_text = ", ".join(detail_parts) if detail_parts else ", ".join(mc["allergy_names"])
        child_parts.append(f"{mc['child'].name}[{detail_text}]")
    staff_title = "⚠️ 알레르기 해당 원생 알림"
    staff_body = f"오늘 식단 알레르기 해당: {', '.join(child_parts)}"
    for sid in staff_ids:
        _notify_user(sid, "allergy_alert", staff_title, staff_body)

def check_allergies():
    """오늘 식단 vs 아이 알레르기 매칭 후 알림 전송 (식단명 포함)"""
    today = datetime.datetime.now(KST).date()

    meals = list(Meals.select().where(Meals.meal_date == today))
    if not meals:
        return {"message": "오늘 등록된 식단이 없습니다.", "checked_servers": 0}

    # 알레르기 번호 → 주의식품 키워드 매핑 (전역 1회)
    num_to_foods = _build_allergy_food_map()

    # 서버별 식단 그룹핑
    server_meals = {}
    for meal in meals:
        sid = meal.server_id
        if sid not in server_meals:
            server_meals[sid] = []
        server_meals[sid].append(meal)

    results = []

    for server_id, meal_list in server_meals.items():
        # 오늘 식단의 알레르기 번호 수집 + 전체 content
        today_allergy_nums = set()
        all_content = ""
        for meal in meal_list:
            all_content += " " + (meal.content or "")
            if meal.allergy_numbers:
                try:
                    nums = json.loads(meal.allergy_numbers)
                    today_allergy_nums.update(nums)
                except Exception:
                    pass

        if not today_allergy_nums:
            results.append({"server_id": server_id, "matched": 0})
            continue

        # 서버 내 승인된 부모 조회
        parent_rows = ServerMembers.select(ServerMembers.user_id).where(
            (ServerMembers.server_id == server_id) &
            (ServerMembers.role == "parent")
        )
        parent_ids = [r.user_id for r in parent_rows]

        if not parent_ids:
            results.append({"server_id": server_id, "matched": 0})
            continue

        approved_parents = list(Users.select(Users.id).where(
            Users.id.in_(parent_ids),
            Users.approved == True
        ))
        approved_ids = [p.id for p in approved_parents]

        if not approved_ids:
            results.append({"server_id": server_id, "matched": 0})
            continue

        # 아이 목록 조회
        children = list(Children.select().where(
            Children.user_id.in_(approved_ids)
        ))

        matched_children = []
        for child in children:
            child_allergy_rows = list(ChildAllergies.select().where(
                ChildAllergies.child_id == child.id
            ))

            child_allergy_nums = set()
            for ca in child_allergy_rows:
                if ca.allergy_type == '기타' and ca.other_detail:
                    # '기타' 타입: other_detail 텍스트를 매핑에서 검색
                    detail = ca.other_detail.strip()
                    found = ALLERGY_TYPE_TO_NUMBERS.get(detail, [])
                    if found:
                        child_allergy_nums.update(found)
                    else:
                        # 부분 매칭 시도 (예: '닭고기, 새우' → 분리)
                        for part in re.split(r'[,\s/]+', detail):
                            part = part.strip()
                            if part:
                                nums = ALLERGY_TYPE_TO_NUMBERS.get(part, [])
                                child_allergy_nums.update(nums)
                else:
                    nums = ALLERGY_TYPE_TO_NUMBERS.get(ca.allergy_type, [])
                    child_allergy_nums.update(nums)

            matching = today_allergy_nums & child_allergy_nums
            if matching:
                allergy_names = [ALLERGY_MAP.get(n, str(n)) for n in sorted(matching)]
                dish_details = _find_dish_names(all_content, matching, num_to_foods)
                matched_children.append({
                    "child": child,
                    "parent_user_id": child.user_id,
                    "allergy_names": allergy_names,
                    "dish_details": dish_details
                })

        if matched_children:
            _notify_allergy_matches(server_id, matched_children)

        results.append({"server_id": server_id, "matched": len(matched_children)})

    return {"message": "알레르기 체크 완료", "checked_servers": len(results)}

def cleanup_meal_files():
    """매월 1일: 전월 이전 식단 파일 자동 삭제"""
    today = datetime.datetime.now(KST).date()
    current_month = today.strftime("%Y-%m")

    base_fs = wiz.project.fs("data", "meal_files")
    base_path = base_fs.abspath()
    if not os.path.isdir(base_path):
        return {"message": "meal_files 디렉토리 없음", "cleaned": 0}

    total_removed = 0
    for server_dir in os.listdir(base_path):
        server_path = os.path.join(base_path, server_dir)
        if not os.path.isdir(server_path):
            continue

        meta_path = os.path.join(server_path, "meta.json")
        if not os.path.isfile(meta_path):
            continue

        try:
            with open(meta_path, 'r') as f:
                meta = json.loads(f.read())
        except Exception:
            continue

        keep = []
        for entry in meta:
            tm = entry.get('target_month') or entry.get('month', '')
            if tm and tm < current_month:
                # 전월 이전 파일 삭제
                try:
                    fpath = os.path.join(server_path, entry['file_name'])
                    if os.path.isfile(fpath):
                        os.remove(fpath)
                    total_removed += 1
                except Exception:
                    pass
            else:
                keep.append(entry)

        if len(keep) != len(meta):
            with open(meta_path, 'w') as f:
                f.write(json.dumps(keep, ensure_ascii=False))

    return {"message": "파일 정리 완료", "removed": total_removed}

# --- Route 분기 ---
segment = wiz.request.match("/api/scheduler/<action>")
if not segment:
    wiz.response.status(404)

action = segment.action

# API 키 인증
key = wiz.request.query("key", "")
if key != SCHEDULER_KEY:
    wiz.response.status(403, message="Invalid scheduler key")

if action == "allergy-check":
    try:
        result = check_allergies()
    except Exception as e:
        wiz.response.status(500, message=str(e))
    wiz.response.status(200, **result)

if action == "cleanup-meal-files":
    try:
        result = cleanup_meal_files()
    except Exception as e:
        wiz.response.status(500, message=str(e))
    wiz.response.status(200, **result)

wiz.response.status(404)
