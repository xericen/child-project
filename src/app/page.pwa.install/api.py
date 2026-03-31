Users = wiz.model("db/login_db/users")

def mark_installed():
    user_id = wiz.session.get("id")
    if not user_id:
        wiz.response.status(401, message="로그인이 필요합니다.")
    try:
        Users.update(app_installed=True).where(Users.id == user_id).execute()
    except Exception as e:
        wiz.response.status(500, message=str(e))
    wiz.response.status(200)
