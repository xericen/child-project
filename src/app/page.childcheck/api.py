import json

Users = wiz.model("db/login_db/users")
Children = wiz.model("db/childcheck/children")
ChildAllergies = wiz.model("db/childcheck/child_allergies")

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
    wiz.response.status(200, hasCompletedAllergyCheck=True)
