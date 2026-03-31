import random
import string
import time
import smtplib
from email.mime.text import MIMEText

Users = wiz.model("db/login_db/users")

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

def _build_code_html(code, purpose="비밀번호 재설정"):
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
    nickname = wiz.request.query("nickname", True)
    email = wiz.request.query("email", True)

    try:
        user = Users.select().where(
            (Users.email == email) & (Users.nickname == nickname)
        ).first()
    except Exception as e:
        wiz.response.status(500, message="DB 조회 오류: " + str(e))

    if not user:
        wiz.response.status(400, message="일치하는 사용자 정보가 없습니다.")

    if not user.verified:
        wiz.response.status(400, message="이메일 인증이 완료되지 않은 계정입니다.")

    code = ''.join(random.choices(string.digits, k=6))

    wiz.session.set(forgot_code=code)
    wiz.session.set(forgot_email=email)
    wiz.session.set(forgot_code_time=str(time.time()))

    try:
        _send_email(
            to=email,
            title="[child] 비밀번호 재설정 인증코드",
            html=_build_code_html(code, "비밀번호 재설정")
        )
    except Exception as e:
        print("[FORGOT] 이메일 발송 실패:", str(e))
        wiz.response.status(500, message="이메일 발송에 실패했습니다. 잠시 후 다시 시도해주세요.")

    wiz.response.status(200, email_sent=True)

def resend_code():
    saved_email = wiz.session.get("forgot_email")
    if not saved_email:
        wiz.response.status(400, message="세션이 만료되었습니다. 다시 시도해주세요.")

    code = ''.join(random.choices(string.digits, k=6))
    wiz.session.set(forgot_code=code)
    wiz.session.set(forgot_code_time=str(time.time()))

    try:
        _send_email(
            to=saved_email,
            title="[child] 비밀번호 재설정 인증코드 (재전송)",
            html=_build_code_html(code, "비밀번호 재설정")
        )
    except Exception as e:
        print("[FORGOT] 재전송 이메일 발송 실패:", str(e))
        wiz.response.status(500, message="이메일 발송에 실패했습니다. 잠시 후 다시 시도해주세요.")

    wiz.response.status(200, email_sent=True)

def verify_code():
    code = wiz.request.query("code", True)

    saved_code = wiz.session.get("forgot_code")
    saved_email = wiz.session.get("forgot_email")
    code_time = wiz.session.get("forgot_code_time")

    if not saved_code or code != saved_code:
        wiz.response.status(400, message="인증코드가 올바르지 않습니다.")

    if not saved_email:
        wiz.response.status(400, message="세션이 만료되었습니다. 다시 시도해주세요.")

    # 만료 시간 검증 (10분)
    if code_time:
        elapsed = time.time() - float(code_time)
        if elapsed > CODE_EXPIRE_SECONDS:
            wiz.session.delete("forgot_code")
            wiz.session.delete("forgot_code_time")
            wiz.response.status(400, message="인증코드가 만료되었습니다. 다시 발송해주세요.")

    wiz.session.set(forgot_verified=True)

    wiz.response.status(200)

def reset_password():
    password = wiz.request.query("password", True)

    verified = wiz.session.get("forgot_verified")
    saved_email = wiz.session.get("forgot_email")

    if not verified or not saved_email:
        wiz.response.status(400, message="인증이 완료되지 않았습니다. 다시 시도해주세요.")

    try:
        user = Users.select().where(Users.email == saved_email).first()
    except Exception as e:
        wiz.response.status(500, message="DB 조회 오류: " + str(e))

    if not user:
        wiz.response.status(400, message="사용자를 찾을 수 없습니다.")

    try:
        Users.update(password=password).where(Users.email == saved_email).execute()
    except Exception as e:
        wiz.response.status(500, message="비밀번호 변경 오류: " + str(e))

    wiz.session.delete("forgot_code")
    wiz.session.delete("forgot_email")
    wiz.session.delete("forgot_verified")
    wiz.session.delete("forgot_code_time")

    wiz.response.status(200)
