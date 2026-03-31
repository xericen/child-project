import random
import string
import time
import smtplib
from email.mime.text import MIMEText

Users = wiz.model("db/login_db/users")
ServerMembers = wiz.model("db/login_db/server_members")
Notifications = wiz.model("db/childcheck/notifications")
push = wiz.model("push")

CODE_EXPIRE_SECONDS = 600  # 10분

def _send_email(to, title, html):
    config = wiz.config("season")
    msg = MIMEText(html, 'html', _charset='utf8')
    msg['Subject'] = title
    msg['From'] = config.smtp_sender
    msg['To'] = to
    server = smtplib.SMTP(config.smtp_host, int(config.smtp_port))
    server.ehlo()
    server.starttls()
    server.login(config.smtp_sender, config.smtp_password)
    server.sendmail(config.smtp_sender, to, msg.as_string())
    server.quit()

def _build_code_html(code, purpose="회원가입"):
    return f"""<div style="width:100%;min-height:100%;background:#eef0fb;padding:40px 0;">
  <div style="max-width:420px;margin:0 auto;background:#fff;border-radius:20px;overflow:hidden;box-shadow:0 4px 24px rgba(91,110,245,0.10);">
    <div style="background:linear-gradient(135deg,#5b6ef5,#7b5ea7);padding:28px 24px;text-align:center;">
      <h1 style="color:#fff;font-size:28px;font-weight:800;margin:0;letter-spacing:-0.5px;">child</h1>
      <p style="color:rgba(255,255,255,0.85);font-size:13px;margin:6px 0 0;">어린이집 알림장</p>
    </div>
    <div style="padding:32px 28px;text-align:center;">
      <p style="font-size:15px;color:#333;margin:0 0 8px;font-weight:600;">{purpose} 인증코드</p>
      <p style="font-size:13px;color:#888;margin:0 0 24px;">아래 인증코드를 입력해주세요.</p>
      <div style="background:#f0f2ff;border-radius:14px;padding:20px;margin:0 0 20px;">
        <span style="font-size:32px;font-weight:800;color:#5b6ef5;letter-spacing:8px;">{code}</span>
      </div>
      <p style="font-size:12px;color:#aaa;margin:0;">이 코드는 <strong style="color:#5b6ef5;">10분간</strong> 유효합니다.</p>
    </div>
    <div style="padding:16px 24px;background:#f8f9fc;text-align:center;border-top:1px solid #eee;">
      <p style="font-size:11px;color:#bbb;margin:0;">본인이 요청하지 않은 경우 이 메일을 무시하셔도 됩니다.</p>
    </div>
  </div>
</div>"""

def get_server_info():
    server_id = wiz.session.get("join_server_id")
    server_name = wiz.session.get("join_server_name")

    if not server_id:
        wiz.response.status(400, message="서버 정보가 없습니다.")

    wiz.response.status(200, server_id=server_id, server_name=server_name)

def send_code():
    # Step 1,2 데이터 수신
    email = wiz.request.query("email", True)
    password = wiz.request.query("password", True)
    nickname = wiz.request.query("nickname", True)
    role = wiz.request.query("role", True)
    phone = wiz.request.query("phone", "")
    child_name = wiz.request.query("child_name", "")
    child_birth_date = wiz.request.query("child_birth_date", "")
    class_name = wiz.request.query("class_name", "")

    server_id = wiz.session.get("join_server_id")
    if not server_id:
        wiz.response.status(400, message="서버를 먼저 선택해주세요.")

    # 같은 서버 내 이메일/전화번호 중복 검사
    try:
        server_member_ids = [m.user_id for m in ServerMembers.select(ServerMembers.user_id).where(
            ServerMembers.server_id == int(server_id)
        )]
    except Exception as e:
        wiz.response.status(500, message="서버 멤버 조회 오류: " + str(e))

    if server_member_ids:
        # 이메일 중복 검사 (서버 내)
        try:
            existing_email = Users.select().where(
                Users.id.in_(server_member_ids),
                Users.email == email
            ).first()
        except Exception as e:
            wiz.response.status(500, message="DB 조회 오류: " + str(e))
        if existing_email:
            wiz.response.status(400, message="이미 해당 서버에 등록된 이메일입니다.")

        # 전화번호 중복 검사 (서버 내, 전화번호가 있는 경우만)
        if phone:
            try:
                existing_phone = Users.select().where(
                    Users.id.in_(server_member_ids),
                    Users.phone == phone
                ).first()
            except Exception as e:
                wiz.response.status(500, message="DB 조회 오류: " + str(e))
            if existing_phone:
                wiz.response.status(400, message="이미 해당 서버에 등록된 전화번호입니다.")

    # 전역 이메일 중복 확인
    try:
        existing = Users.select().where(Users.email == email).first()
    except Exception as e:
        wiz.response.status(500, message="DB 조회 오류: " + str(e))

    if existing:
        wiz.response.status(400, message="이미 가입된 이메일입니다.")

    # 가입 정보를 세션에 임시 저장 (인증 완료 전까지 DB에 저장하지 않음)
    signup_data = dict(
        email=email,
        password=password,
        nickname=nickname,
        phone=phone,
        role=role,
        class_name=class_name,
    )
    if role == "parent":
        signup_data["child_name"] = child_name
        if child_birth_date:
            signup_data["birth_date"] = child_birth_date

    import json
    wiz.session.set(signup_data=json.dumps(signup_data))

    # 인증코드 생성
    code = ''.join(random.choices(string.digits, k=6))

    # 세션에 인증코드/이메일/생성시각 저장
    wiz.session.set(signup_code=code)
    wiz.session.set(signup_email=email)
    wiz.session.set(signup_code_time=str(time.time()))

    # 이메일 발송 시도
    try:
        _send_email(
            to=email,
            title="[child] 회원가입 인증코드",
            html=_build_code_html(code, "회원가입")
        )
    except Exception as e:
        import traceback
        print("[SIGNUP] 이메일 발송 실패:", str(e), "TRACEBACK:", traceback.format_exc())
        wiz.response.status(500, message="이메일 발송에 실패했습니다. 잠시 후 다시 시도해주세요.")

    wiz.response.status(200, email_sent=True)

def resend_code():
    saved_email = wiz.session.get("signup_email")
    if not saved_email:
        wiz.response.status(400, message="세션이 만료되었습니다. 다시 시도해주세요.")

    # 새 인증코드 생성 (기존 코드 무효화)
    code = ''.join(random.choices(string.digits, k=6))
    wiz.session.set(signup_code=code)
    wiz.session.set(signup_code_time=str(time.time()))

    # 이메일 발송 시도
    try:
        _send_email(
            to=saved_email,
            title="[child] 회원가입 인증코드 (재전송)",
            html=_build_code_html(code, "회원가입")
        )
    except Exception as e:
        print("[SIGNUP] 이메일 재전송 실패:", str(e))
        wiz.response.status(500, message="이메일 발송에 실패했습니다. 잠시 후 다시 시도해주세요.")

    wiz.response.status(200, email_sent=True)

def notify_directors(server_id, user_nickname, user_role):
    role_label = "교사" if user_role == "teacher" else "학부모" if user_role == "parent" else user_role
    try:
        director_ids = [m.user_id for m in ServerMembers.select(ServerMembers.user_id).where(
            ServerMembers.server_id == int(server_id)
        )]
        if not director_ids:
            return
        directors = Users.select(Users.id).where(
            Users.id.in_(director_ids),
            Users.role == "director"
        )
        for d in directors:
            Notifications.create(
                user_id=d.id,
                type="approval",
                title="새 회원가입 승인 요청",
                message=f"{user_nickname}({role_label})님이 가입했습니다.",
                link="/note/approve"
            )
            try:
                push.send_to_user(d.id, "새 회원가입 승인 요청", f"{user_nickname}({role_label})님이 가입했습니다.", url="/note/approve", noti_type="approval")
            except Exception:
                pass
    except Exception:
        pass

def verify_code():
    invite_code = wiz.request.query("invite_code", True)

    saved_code = wiz.session.get("signup_code")
    saved_email = wiz.session.get("signup_email")
    server_id = wiz.session.get("join_server_id")
    signup_data_json = wiz.session.get("signup_data")
    code_time = wiz.session.get("signup_code_time")

    if not saved_code or invite_code != saved_code:
        wiz.response.status(400, message="인증코드가 올바르지 않습니다.")

    # 만료 시간 검증 (10분)
    if code_time:
        elapsed = time.time() - float(code_time)
        if elapsed > CODE_EXPIRE_SECONDS:
            wiz.session.delete("signup_code")
            wiz.session.delete("signup_code_time")
            wiz.response.status(400, message="인증코드가 만료되었습니다. 다시 발송해주세요.")

    if not server_id:
        wiz.response.status(400, message="서버 정보가 없습니다. 다시 시도해주세요.")

    if not signup_data_json:
        wiz.response.status(400, message="가입 정보가 없습니다. 처음부터 다시 시도해주세요.")

    import json
    signup_data = json.loads(signup_data_json)

    # 이메일 중복 재확인 (인증 지연 사이 다른 사용자가 같은 이메일로 가입할 수 있으므로)
    try:
        existing = Users.select().where(Users.email == saved_email).first()
    except Exception as e:
        wiz.response.status(500, message="DB 조회 오류: " + str(e))

    if existing:
        wiz.response.status(400, message="이미 가입된 이메일입니다.")

    # 인증 완료 후 사용자 생성
    signup_data["verified"] = True
    signup_data["approved"] = False
    try:
        user = Users.create(**signup_data)
    except Exception as e:
        wiz.response.status(500, message="사용자 생성 오류: " + str(e))

    # 서버 멤버로 등록
    try:
        ServerMembers.create(
            server_id=int(server_id),
            user_id=user.id,
            role=signup_data["role"]
        )
    except Exception as e:
        wiz.response.status(500, message="서버 멤버 등록 오류: " + str(e))

    # 원장에게 가입 승인 알림
    notify_directors(server_id, signup_data["nickname"], signup_data["role"])

    # 인증용 세션 정리
    wiz.session.delete("signup_code")
    wiz.session.delete("signup_email")
    wiz.session.delete("signup_data")
    wiz.session.delete("signup_code_time")

    # 로그인 세션을 설정하지 않음 - 원장 승인 대기
    wiz.response.status(200)
