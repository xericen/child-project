Users = wiz.model("db/login_db/users")
ServerMembers = wiz.model("db/login_db/server_members")
Servers = wiz.model("db/login_db/servers")
Children = wiz.model("db/childcheck/children")
push = wiz.model("push")

def data():
    wiz.response.status(200)

def get_server_info():
    server_id = wiz.session.get("join_server_id")
    server_name = wiz.session.get("join_server_name")

    # Fallback: 세션에 없으면 request param에서 읽어 세션에 저장
    if not server_id:
        server_id = wiz.request.query("server_id", None)
        server_name = wiz.request.query("server_name", None)
        if server_id:
            wiz.session.set(join_server_id=server_id)
            wiz.session.set(join_server_name=server_name)

    if not server_id:
        wiz.response.status(400, message="서버 정보가 없습니다.")

    wiz.response.status(200, server_id=server_id, server_name=server_name)

def mark_installed():
    user_id = wiz.session.get("id")
    if not user_id:
        wiz.response.status(401, message="로그인이 필요합니다.")
    try:
        Users.update(app_installed=True).where(Users.id == user_id).execute()
    except Exception as e:
        wiz.response.status(500, message=str(e))
    wiz.response.status(200)

def get_vapid_key():
    push_config = wiz.config("push")
    wiz.response.status(200, public_key=push_config.vapid.public_key)

def subscribe_push():
    user_id = wiz.session.get("id")
    if not user_id:
        wiz.response.status(401, message="로그인이 필요합니다.")
    endpoint = wiz.request.query("endpoint", True)
    p256dh = wiz.request.query("p256dh", True)
    auth = wiz.request.query("auth", True)
    device_type = wiz.request.query("device_type", "unknown")
    try:
        push.subscribe(user_id, endpoint, p256dh, auth, device_type)
    except Exception as e:
        wiz.response.status(500, message=str(e))
    wiz.response.status(200)

def _get_allergy_check_completed(user):
    try:
        child = Children.select().where(Children.user_id == user.id).first()
        if child is None:
            return False
        return bool(child.allergy_checked)
    except Exception:
        return False

def login():
    email = wiz.request.query("email", True)
    password = wiz.request.query("password", True)

    server_id = wiz.session.get("join_server_id")
    if not server_id:
        wiz.response.status(400, message="서버를 먼저 선택해주세요.")

    try:
        user = Users.select().where(Users.email == email).first()
    except Exception as e:
        wiz.response.status(500, message="DB 조회 오류: " + str(e))

    if not user:
        wiz.response.status(400, message="이메일이 존재하지 않습니다.")

    if user.password != password:
        wiz.response.status(400, message="비밀번호가 올바르지 않습니다.")

    if not user.verified:
        wiz.response.status(400, message="이메일 인증이 완료되지 않은 계정입니다.")

    # 서버 멤버십 확인: 해당 서버에 가입된 사용자인지 검증
    try:
        membership = ServerMembers.select().where(
            (ServerMembers.server_id == int(server_id)) &
            (ServerMembers.user_id == user.id)
        ).first()
    except Exception as e:
        wiz.response.status(500, message="멤버십 조회 오류: " + str(e))

    if not membership:
        wiz.response.status(400, message="해당 어린이집에 가입되어 있지 않습니다. 회원가입을 먼저 진행해주세요.")

    # 원장(director)은 승인 체크 불필요 (서버 생성 시 자동 승인됨)
    # 교사/부모는 원장 승인 필요
    if user.role != 'director' and not user.approved:
        wiz.response.status(400, message="원장의 승인을 기다리고 있습니다. 승인 후 로그인이 가능합니다.")

    # 어린이집 이름: 세션에서 먼저 시도, 없으면 DB 조회
    server_name = wiz.session.get("join_server_name") or ""
    if not server_name:
        try:
            server = Servers.select(Servers.name).where(Servers.id == int(server_id)).first()
            if server:
                server_name = server.name or ""
        except Exception:
            pass

    wiz.session.set(id=user.id)
    wiz.session.set(email=user.email)
    wiz.session.set(role=user.role)
    wiz.session.set(nickname=user.nickname)
    wiz.session.set(server_id=int(server_id))
    wiz.session.set(join_server_name=server_name)

    childcheck_done = True
    if user.role == "parent":
        childcheck_done = _get_allergy_check_completed(user)

    wiz.response.status(
        200,
        role=user.role,
        childcheck_done=childcheck_done,
        hasCompletedAllergyCheck=childcheck_done,
        app_installed=bool(user.app_installed)
    )
