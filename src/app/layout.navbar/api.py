Children = wiz.model("db/childcheck/children")

def check_childcheck():
    role = wiz.session.get("role")
    user_id = wiz.session.get("id")
    if role != "parent" or not user_id:
        wiz.response.status(200, need_childcheck=False)
    try:
        child = Children.select().where(Children.user_id == int(user_id)).first()
        if child is None or not child.allergy_checked:
            wiz.response.status(200, need_childcheck=True)
    except Exception:
        wiz.response.status(200, need_childcheck=True)
    wiz.response.status(200, need_childcheck=False)
