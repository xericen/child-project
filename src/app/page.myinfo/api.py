import json
import traceback

Users = wiz.model("db/login_db/users")
Servers = wiz.model("db/login_db/servers")
Children = wiz.model("db/childcheck/children")
ChildAllergies = wiz.model("db/childcheck/child_allergies")

def get_myinfo():
    user_id = wiz.session.get("id")
    if not user_id:
        wiz.response.status(401, message="로그인이 필요합니다.")

    try:
        user = Users.select().where(Users.id == int(user_id)).first()
    except Exception as e:
        wiz.response.status(500, message=str(e))

    if not user:
        wiz.response.status(400, message="사용자를 찾을 수 없습니다.")

    result = {
        "email": user.email,
        "role": user.role,
        "nickname": user.nickname or "",
        "phone": user.phone or "",
        "child_name": user.child_name or "",
        "birth_date": "",
        "twin_type": "없음",
        "allergies": [],
        "server_code": "",
        "debug_user_id": str(user_id),
        "debug_user_role": user.role
    }

    # 원장인 경우 서버 코드 조회
    if user.role == "director":
        server = None
        debug_info = {"user_id": str(user_id), "user_role": user.role}
        # 1차: 세션 server_id로 조회
        server_id = wiz.session.get("server_id") or wiz.session.get("join_server_id")
        debug_info["session_server_id"] = str(server_id)
        if server_id:
            try:
                server = Servers.select().where(Servers.id == int(server_id)).first()
                debug_info["server_by_session"] = server is not None
            except Exception as e:
                debug_info["server_by_session_error"] = str(e)
        # 2차: director_id로 조회
        if not server:
            try:
                server = Servers.select().where(Servers.director_id == int(user_id)).first()
                debug_info["server_by_director"] = server is not None
            except Exception as e:
                debug_info["server_by_director_error"] = str(e)
        if server:
            debug_info["server_code_value"] = server.server_code
            debug_info["server_name"] = server.name
            result["server_code"] = server.server_code or ""
        else:
            debug_info["server_found"] = False
        result["debug_server"] = debug_info

    try:
        child = Children.select().where(Children.user_id == int(user_id)).first()
        if child:
            result["birth_date"] = str(child.birthdate) if child.birthdate else ""
            result["twin_type"] = child.twin_type or "없음"

            allergies = ChildAllergies.select().where(ChildAllergies.child_id == child.id)
            for a in allergies:
                result["allergies"].append({
                    "allergy_type": a.allergy_type,
                    "other_detail": a.other_detail or "",
                    "is_severe": a.is_severe,
                    "needs_substitute": a.needs_substitute
                })
    except Exception:
        pass

    wiz.response.status(200, **result)

def save_myinfo():
    user_id = wiz.session.get("id")
    if not user_id:
        wiz.response.status(401, message="로그인이 필요합니다.")

    nickname = wiz.request.query("nickname", "")
    phone = wiz.request.query("phone", "")
    birth_date = wiz.request.query("birth_date", "")
    twin_type = wiz.request.query("twin_type", "없음")
    allergies_json = wiz.request.query("allergies", "[]")
    is_severe = wiz.request.query("is_severe", "false") == "true"
    needs_substitute = wiz.request.query("needs_substitute", "false") == "true"

    try:
        allergies = json.loads(allergies_json)
    except Exception:
        allergies = []

    # 사용자 기본 정보 업데이트 (이름, 전화번호 - 모든 역할)
    update_data = {}
    if nickname:
        update_data["nickname"] = nickname
    update_data["phone"] = phone if phone else None

    try:
        if update_data:
            Users.update(**update_data).where(Users.id == int(user_id)).execute()
    except Exception as e:
        wiz.response.status(500, message="사용자 정보 수정 오류: " + str(e))

    # 자녀 관련 정보 업데이트 (부모만)
    try:
        child = Children.select().where(Children.user_id == int(user_id)).first()
    except Exception:
        child = None

    if child:
        try:
            Children.update(
                birthdate=birth_date if birth_date else None,
                twin_type=twin_type
            ).where(Children.id == child.id).execute()
        except Exception as e:
            wiz.response.status(500, message="자녀 정보 수정 오류: " + str(e))

        try:
            ChildAllergies.delete().where(ChildAllergies.child_id == child.id).execute()
        except Exception:
            pass

        for allergy in allergies:
            allergy_type = allergy.get("allergy_type", "")
            other_detail = allergy.get("other_detail", "")
            if allergy_type:
                try:
                    ChildAllergies.create(
                        child_id=child.id,
                        allergy_type=allergy_type,
                        other_detail=other_detail,
                        is_severe=is_severe,
                        needs_substitute=needs_substitute
                    )
                except Exception as e:
                    pass

    wiz.response.status(200)

def change_password():
    user_id = wiz.session.get("id")
    if not user_id:
        wiz.response.status(401, message="로그인이 필요합니다.")

    current_password = wiz.request.query("current_password", True)
    new_password = wiz.request.query("new_password", True)

    if len(new_password) < 4:
        wiz.response.status(400, message="새 비밀번호는 4자 이상이어야 합니다.")

    try:
        user = Users.select().where(Users.id == int(user_id)).first()
    except Exception as e:
        wiz.response.status(500, message=str(e))

    if not user:
        wiz.response.status(400, message="사용자를 찾을 수 없습니다.")

    if user.password != current_password:
        wiz.response.status(400, message="현재 비밀번호가 올바르지 않습니다.")

    try:
        Users.update(password=new_password).where(Users.id == int(user_id)).execute()
    except Exception as e:
        wiz.response.status(500, message=str(e))

    wiz.response.status(200)
