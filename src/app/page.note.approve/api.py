Users = wiz.model("db/login_db/users")
ServerMembers = wiz.model("db/login_db/server_members")
Children = wiz.model("db/childcheck/children")
ChildAllergies = wiz.model("db/childcheck/child_allergies")

def get_pending_users():
    role = wiz.session.get("role")
    if role != "director":
        wiz.response.status(403, message="접근 권한이 없습니다.")

    server_id = wiz.session.get("server_id")
    if not server_id:
        wiz.response.status(400, message="서버 정보가 없습니다.")

    # 현재 서버에 소속된 멤버 중 미승인+인증완료 사용자만 조회
    try:
        members = ServerMembers.select(ServerMembers.user_id).where(
            ServerMembers.server_id == int(server_id)
        )
        member_user_ids = [m.user_id for m in members]
    except Exception as e:
        wiz.response.status(500, message="멤버 조회 오류: " + str(e))

    if not member_user_ids:
        wiz.response.status(200, users=[])

    try:
        rows = Users.select().where(
            (Users.id.in_(member_user_ids)) &
            (Users.approved == False) &
            (Users.verified == True) &
            (Users.role != "director")
        )
    except Exception as e:
        wiz.response.status(500, message="DB 조회 오류: " + str(e))

    result = []
    for user in rows:
        result.append(dict(
            id=user.id,
            nickname=user.nickname,
            email=user.email,
            role=user.role,
            class_name=user.class_name or "",
            child_name=user.child_name or ""
        ))

    wiz.response.status(200, users=result)

def approve_user():
    role = wiz.session.get("role")
    if role != "director":
        wiz.response.status(403, message="접근 권한이 없습니다.")

    server_id = wiz.session.get("server_id")
    if not server_id:
        wiz.response.status(400, message="서버 정보가 없습니다.")

    user_id = wiz.request.query("user_id", True)

    try:
        user_id = int(user_id)
    except Exception:
        wiz.response.status(400, message="잘못된 사용자 ID입니다.")

    # 해당 유저가 현재 서버 멤버인지 확인
    try:
        membership = ServerMembers.select().where(
            (ServerMembers.server_id == int(server_id)) &
            (ServerMembers.user_id == user_id)
        ).first()
    except Exception as e:
        wiz.response.status(500, message="멤버십 조회 오류: " + str(e))

    if not membership:
        wiz.response.status(400, message="해당 서버의 멤버가 아닙니다.")

    try:
        Users.update(approved=True).where(Users.id == user_id).execute()
    except Exception as e:
        wiz.response.status(500, message="승인 처리 오류: " + str(e))

    # 부모인 경우 children 레코드 자동 생성
    try:
        user = Users.select().where(Users.id == user_id).first()
        if user and user.role == "parent" and user.child_name:
            existing = Children.select().where(Children.user_id == user_id).first()
            if not existing:
                Children.create(
                    user_id=user_id,
                    name=user.child_name,
                    birthdate=user.birth_date,
                    twin_type="없음"
                )
    except Exception as e:
        print("[APPROVE] children 생성 오류:", str(e))

    wiz.response.status(200)

def reject_user():
    role = wiz.session.get("role")
    if role != "director":
        wiz.response.status(403, message="접근 권한이 없습니다.")

    server_id = wiz.session.get("server_id")
    if not server_id:
        wiz.response.status(400, message="서버 정보가 없습니다.")

    user_id = wiz.request.query("user_id", True)

    try:
        user_id = int(user_id)
    except Exception:
        wiz.response.status(400, message="잘못된 사용자 ID입니다.")

    # 해당 유저가 현재 서버 멤버인지 확인
    try:
        membership = ServerMembers.select().where(
            (ServerMembers.server_id == int(server_id)) &
            (ServerMembers.user_id == user_id)
        ).first()
    except Exception as e:
        wiz.response.status(500, message="멤버십 조회 오류: " + str(e))

    if not membership:
        wiz.response.status(400, message="해당 서버의 멤버가 아닙니다.")

    # 서버 멤버에서 제거
    try:
        ServerMembers.delete().where(
            (ServerMembers.server_id == int(server_id)) &
            (ServerMembers.user_id == user_id)
        ).execute()
    except Exception as e:
        print("[REJECT] 서버 멤버 삭제 오류:", str(e))

    # 연관 데이터 cascade 삭제: child_allergies → children → user
    try:
        children = Children.select(Children.id).where(Children.user_id == user_id)
        child_ids = [c.id for c in children]
        if child_ids:
            ChildAllergies.delete().where(ChildAllergies.child_id.in_(child_ids)).execute()
            Children.delete().where(Children.user_id == user_id).execute()
    except Exception as e:
        print("[REJECT] 연관 데이터 삭제 오류:", str(e))

    try:
        Users.delete().where(Users.id == user_id).execute()
    except Exception as e:
        wiz.response.status(500, message="거절 처리 오류: " + str(e))

    wiz.response.status(200)
