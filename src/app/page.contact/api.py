Users = wiz.model("db/login_db/users")
Servers = wiz.model("db/login_db/servers")
ServerMembers = wiz.model("db/login_db/server_members")

def get_contacts():
    user_id = wiz.session.get("id")
    server_id = wiz.session.get("server_id") or wiz.session.get("join_server_id")
    if not user_id or not server_id:
        wiz.response.status(401)

    contacts = []

    try:
        server = Servers.select().where(Servers.id == int(server_id)).first()
        if server and server.director_id:
            director = Users.select().where(Users.id == server.director_id).first()
            if director:
                contacts.append({
                    "role": "원장",
                    "name": director.nickname or "",
                    "phone": director.phone or ""
                })
    except Exception:
        pass

    try:
        user = Users.select().where(Users.id == int(user_id)).first()
        parent_class = ""
        if user:
            parent_class = (user.class_name or "").strip()

        if parent_class:
            teacher_members = ServerMembers.select(ServerMembers.user_id).where(
                (ServerMembers.server_id == int(server_id)) & (ServerMembers.role == "teacher")
            )
            teacher_ids = [m.user_id for m in teacher_members]
            if teacher_ids:
                teachers = Users.select().where(
                    (Users.id.in_(teacher_ids)) & (Users.class_name == parent_class)
                )
                for t in teachers:
                    contacts.append({
                        "role": "담당 교사",
                        "name": t.nickname or "",
                        "phone": t.phone or ""
                    })
    except Exception:
        pass

    wiz.response.status(200, contacts=contacts)
