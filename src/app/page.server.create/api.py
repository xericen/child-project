import random
import string
import smtplib
from email.mime.text import MIMEText

Users = wiz.model("db/login_db/users")
struct = wiz.model("struct")

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

def _build_code_html(code, purpose="서버 생성"):
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

def send_code():
    email = wiz.request.query("email", True)
    password = wiz.request.query("password", True)
    director_name = wiz.request.query("director_name", True)
    phone = wiz.request.query("phone", "")
    server_name = wiz.request.query("server_name", True)

    # 이메일 중복 확인
    try:
        existing = Users.select().where(Users.email == email).first()
    except Exception as e:
        wiz.response.status(500, message="DB 조회 오류: " + str(e))

    if existing:
        wiz.response.status(400, message="이미 가입된 이메일입니다.")

    # 인증코드 생성
    code = ''.join(random.choices(string.digits, k=6))

    # 세션에 정보 저장
    wiz.session.set(server_create_code=code)
    wiz.session.set(server_create_email=email)
    wiz.session.set(server_create_password=password)
    wiz.session.set(server_create_director_name=director_name)
    wiz.session.set(server_create_phone=phone)
    wiz.session.set(server_create_server_name=server_name)

    # 이메일 발송
    try:
        _send_email(
            to=email,
            title="[child] 어린이집 서버 생성 인증코드",
            html=_build_code_html(code, "서버 생성")
        )
    except Exception as e:
        print("[SERVER_CREATE] 이메일 발송 실패:", str(e))
        wiz.response.status(500, message="이메일 발송에 실패했습니다. 잠시 후 다시 시도해주세요.")

    wiz.response.status(200, email_sent=True)

def resend_code():
    saved_email = wiz.session.get("server_create_email")
    if not saved_email:
        wiz.response.status(400, message="세션이 만료되었습니다. 다시 시도해주세요.")

    code = ''.join(random.choices(string.digits, k=6))
    wiz.session.set(server_create_code=code)

    try:
        _send_email(
            to=saved_email,
            title="[child] 어린이집 서버 생성 인증코드 (재전송)",
            html=_build_code_html(code, "서버 생성")
        )
    except Exception as e:
        print("[SERVER_CREATE] 이메일 재전송 실패:", str(e))
        wiz.response.status(500, message="이메일 발송에 실패했습니다. 잠시 후 다시 시도해주세요.")

    wiz.response.status(200, email_sent=True)

def verify_and_create():
    invite_code = wiz.request.query("invite_code", True)

    saved_code = wiz.session.get("server_create_code")
    saved_email = wiz.session.get("server_create_email")
    saved_password = wiz.session.get("server_create_password")
    saved_director_name = wiz.session.get("server_create_director_name")
    saved_phone = wiz.session.get("server_create_phone")
    saved_server_name = wiz.session.get("server_create_server_name")

    if not saved_code or invite_code != saved_code:
        wiz.response.status(400, message="인증코드가 올바르지 않습니다.")

    if not saved_email:
        wiz.response.status(400, message="세션이 만료되었습니다. 다시 시도해주세요.")

    # 1. 원장 계정 생성 (director role, verified=True, approved=True)
    try:
        user = Users.create(
            email=saved_email,
            password=saved_password,
            nickname=saved_director_name,
            phone=saved_phone if saved_phone else None,
            role='director',
            verified=True,
            approved=True
        )
    except Exception as e:
        wiz.response.status(500, message="원장 계정 생성 오류: " + str(e))

    # 2. 서버 생성 + 멤버 등록
    try:
        result = struct.server.create(
            name=saved_server_name,
            director_name=saved_director_name,
            director_id=user.id
        )
    except Exception as e:
        wiz.response.status(500, message="서버 생성 오류: " + str(e))

    # 3. 세션에 서버 정보 저장 (로그인 페이지에서 사용)
    wiz.session.set(join_server_id=result['id'])
    wiz.session.set(join_server_name=result['name'])

    # 세션 정리
    wiz.session.delete("server_create_code")
    wiz.session.delete("server_create_email")
    wiz.session.delete("server_create_password")
    wiz.session.delete("server_create_director_name")
    wiz.session.delete("server_create_phone")
    wiz.session.delete("server_create_server_name")

    wiz.response.status(200, server_code=result['server_code'])
