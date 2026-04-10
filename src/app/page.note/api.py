import os
import datetime
from PIL import Image, ImageOps
import io

Users = wiz.model("db/login_db/users")
Servers = wiz.model("db/login_db/servers")
Children = wiz.model("db/childcheck/children")

MAX_IMAGE_WIDTH = 800
JPEG_QUALITY = 85

def _compress_image(file_data, max_width=MAX_IMAGE_WIDTH, quality=JPEG_QUALITY):
    img = Image.open(io.BytesIO(file_data))
    img = ImageOps.exif_transpose(img)
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')
    w, h = img.size
    if w > max_width:
        ratio = max_width / w
        img = img.resize((max_width, int(h * ratio)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=quality, optimize=True)
    return buf.getvalue()

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

    # 프로필 사진 조회
    profile_photo = ""
    if role == "parent" and user_id:
        try:
            child = Children.select(Children.profile_photo).where(Children.user_id == int(user_id)).first()
            if child and child.profile_photo:
                profile_photo = child.profile_photo
        except Exception:
            pass

    wiz.response.status(200, role=role, child_name=child_name, class_name=class_name, server_name=server_name, childcheck_done=childcheck_done, profile_photo=profile_photo)

def upload_profile_photo():
    role = wiz.session.get("role")
    user_id = wiz.session.get("id")
    if not role or not user_id:
        wiz.response.status(401, message="로그인이 필요합니다.")

    if role != "parent":
        wiz.response.status(403, message="부모만 프로필 사진을 업로드할 수 있습니다.")

    file = wiz.request.file("photo")
    if not file or not file.filename:
        wiz.response.status(400, message="사진을 선택해주세요.")

    try:
        child = Children.select().where(Children.user_id == int(user_id)).first()
    except Exception as e:
        wiz.response.status(400, message=str(e))

    if not child:
        wiz.response.status(400, message="등록된 자녀 정보가 없습니다.")

    fs = wiz.project.fs("data", "profile_photos")
    safe_name = f"child_{child.id}_{int(datetime.datetime.now().timestamp())}.jpg"
    save_path = fs.abspath(safe_name)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    try:
        compressed = _compress_image(file.read())
        with open(save_path, 'wb') as wf:
            wf.write(compressed)
    except Exception as e:
        wiz.response.status(500, message=str(e))

    # 기존 사진 파일 삭제
    old_photo = child.profile_photo
    if old_photo:
        try:
            old_path = fs.abspath(old_photo)
            if os.path.isfile(old_path):
                os.remove(old_path)
        except Exception:
            pass

    # DB 업데이트
    try:
        Children.update(profile_photo=safe_name).where(Children.id == child.id).execute()
    except Exception as e:
        wiz.response.status(500, message=str(e))

    wiz.response.status(200, profile_photo=safe_name)

def serve_profile_photo():
    filename = wiz.request.query("filename", True)
    if ".." in filename or "/" in filename:
        wiz.response.abort(400)

    fs = wiz.project.fs("data", "profile_photos")
    filepath = fs.abspath(filename)
    if not os.path.isfile(filepath):
        wiz.response.abort(404)

    flask = wiz.response._flask
    resp = flask.send_file(filepath, mimetype='image/jpeg')
    resp.headers['Cache-Control'] = 'public, max-age=86400'
    wiz.response.response(resp)

def delete_profile_photo():
    role = wiz.session.get("role")
    user_id = wiz.session.get("id")
    if not role or not user_id:
        wiz.response.status(401, message="로그인이 필요합니다.")

    if role != "parent":
        wiz.response.status(403, message="부모만 프로필 사진을 삭제할 수 있습니다.")

    try:
        child = Children.select().where(Children.user_id == int(user_id)).first()
    except Exception as e:
        wiz.response.status(400, message=str(e))

    if not child or not child.profile_photo:
        wiz.response.status(400, message="삭제할 사진이 없습니다.")

    fs = wiz.project.fs("data", "profile_photos")
    try:
        old_path = fs.abspath(child.profile_photo)
        if os.path.isfile(old_path):
            os.remove(old_path)
    except Exception:
        pass

    try:
        Children.update(profile_photo=None).where(Children.id == child.id).execute()
    except Exception as e:
        wiz.response.status(500, message=str(e))

    wiz.response.status(200)
