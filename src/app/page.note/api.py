Users = wiz.model("db/login_db/users")
Servers = wiz.model("db/login_db/servers")
Children = wiz.model("db/childcheck/children")

def get_role():
    role = wiz.session.get("role")
    if not role:
        wiz.response.status(401, message="로그인이 필요합니다.")

    child_name = ""
    class_name = ""
    server_name = ""
    childcheck_done = True
    user_id = wiz.session.get("id")

    # 부모: childcheck 완료 여부 확인
    if role == "parent" and user_id:
        try:
            child = Children.select().where(Children.user_id == int(user_id)).first()
            if child is None or not child.allergy_checked:
                childcheck_done = False
        except Exception:
            childcheck_done = False

    # 어린이집 이름: 세션에서 먼저 시도, 없으면 DB 조회
    server_name = wiz.session.get("join_server_name") or ""
    if not server_name:
        server_id = wiz.session.get("server_id") or wiz.session.get("join_server_id")
        if server_id:
            try:
                server = Servers.select(Servers.name).where(Servers.id == int(server_id)).first()
                if server:
                    server_name = server.name or ""
                    wiz.session.set(join_server_name=server_name)
            except Exception:
                pass

    if user_id:
        try:
            user = Users.select(Users.child_name, Users.class_name).where(Users.id == int(user_id)).first()
            if user:
                if role == "parent":
                    child_name = user.child_name or ""
                    class_name = user.class_name or ""
                elif role == "teacher":
                    class_name = user.class_name or ""
        except Exception:
            pass

    wiz.response.status(200, role=role, child_name=child_name, class_name=class_name, server_name=server_name, childcheck_done=childcheck_done)
