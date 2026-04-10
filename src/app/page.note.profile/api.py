# pyright: reportUndefinedVariable=false, reportMissingImports=false
import os
import datetime
from PIL import Image, ImageOps
import io

Users = wiz.model("db/login_db/users")
ServerMembers = wiz.model("db/login_db/server_members")
Children = wiz.model("db/childcheck/children")
ChildAllergies = wiz.model("db/childcheck/child_allergies")

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

def get_profile_data():
    role = wiz.session.get("role")
    if not role:
        wiz.response.status(401, message="로그인이 필요합니다.")

    if role == "parent":
        wiz.response.status(403, message="접근 권한이 없습니다.")

    user_id = wiz.session.get("id")
    server_id = wiz.session.get("server_id") or wiz.session.get("join_server_id")

    # 현재 서버 소속 사용자 ID 목록 (서버 격리)
    server_user_ids = []
    if server_id:
        try:
            members = ServerMembers.select(ServerMembers.user_id).where(
                ServerMembers.server_id == int(server_id)
            )
            server_user_ids = [m.user_id for m in members]
        except Exception:
            pass

    # 교사 목록 조회
    teachers = []
    teacher_class = ""

    if role == "teacher":
        try:
            me = Users.select(Users.class_name).where(Users.id == int(user_id)).first()
            if me and me.class_name:
                teacher_class = me.class_name.strip()
        except Exception:
            pass
    else:
        if server_user_ids:
            try:
                teacher_rows = Users.select(Users.id, Users.nickname, Users.class_name, Users.phone).where(
                    Users.id.in_(server_user_ids),
                    Users.role == "teacher"
                )
                for t in teacher_rows:
                    teachers.append(dict(
                        id=t.id,
                        name=t.nickname or "",
                        class_name=(t.class_name or "").strip(),
                        phone=t.phone or ""
                    ))
            except Exception:
                pass

    # 어린이 목록 조회
    children = []
    today = datetime.date.today()

    target_parents = []
    if role == "teacher":
        if teacher_class and server_user_ids:
            try:
                parents = Users.select(Users.id, Users.nickname, Users.class_name, Users.child_name, Users.phone, Users.birth_date).where(
                    Users.id.in_(server_user_ids),
                    Users.role == "parent",
                    Users.approved == True,
                    Users.class_name == teacher_class
                )
                target_parents = list(parents)
            except Exception:
                pass
    else:
        if server_user_ids:
            try:
                parents = Users.select(Users.id, Users.nickname, Users.class_name, Users.child_name, Users.phone, Users.birth_date).where(
                    Users.id.in_(server_user_ids),
                    Users.role == "parent",
                    Users.approved == True
                )
                target_parents = list(parents)
            except Exception:
                pass

    for parent in target_parents:
        child_rows = []
        try:
            child_rows = list(Children.select().where(Children.user_id == parent.id))
        except Exception:
            pass

        if child_rows:
            for child in child_rows:
                age = 0
                birthdate_str = ""
                if child.birthdate:
                    bd = child.birthdate
                    age = today.year - bd.year
                    if (today.month, today.day) < (bd.month, bd.day):
                        age -= 1
                    birthdate_str = str(bd)

                allergies = []
                is_severe = False
                needs_substitute = False
                try:
                    allergy_rows = ChildAllergies.select().where(ChildAllergies.child_id == child.id)
                    for a in allergy_rows:
                        allergies.append(dict(
                            allergy_type=a.allergy_type,
                            other_detail=a.other_detail or ""
                        ))
                        if getattr(a, 'is_severe', False):
                            is_severe = True
                        if getattr(a, 'needs_substitute', False):
                            needs_substitute = True
                except Exception:
                    pass

                is_birthday = False
                if child.birthdate:
                    bd = child.birthdate
                    if today.month == bd.month and today.day == bd.day:
                        is_birthday = True

                children.append(dict(
                    id=child.id,
                    parent_id=parent.id,
                    name=child.name,
                    birthdate=birthdate_str,
                    age=age,
                    twin_type=child.twin_type,
                    class_name=(parent.class_name or "").strip(),
                    nickname=parent.nickname or "",
                    parent_name=parent.nickname or "",
                    parent_phone=parent.phone or "",
                    allergies=allergies,
                    is_severe=is_severe,
                    needs_substitute=needs_substitute,
                    has_childcheck=True,
                    is_birthday=is_birthday,
                    profile_photo=child.profile_photo or ""
                ))
        else:
            child_name = parent.child_name or ""
            if child_name:
                is_birthday = False
                try:
                    bd = parent.birth_date
                    if bd and today.month == bd.month and today.day == bd.day:
                        is_birthday = True
                except Exception:
                    pass
                children.append(dict(
                    id=0,
                    parent_id=parent.id,
                    name=child_name,
                    birthdate="",
                    age=0,
                    twin_type="없음",
                    class_name=(parent.class_name or "").strip(),
                    nickname=parent.nickname or "",
                    parent_name=parent.nickname or "",
                    parent_phone=parent.phone or "",
                    allergies=[],
                    is_severe=False,
                    needs_substitute=False,
                    has_childcheck=False,
                    is_birthday=is_birthday,
                    profile_photo=""
                ))

    # 원장: 반별 그룹핑 데이터 생성
    classes = []
    if role == "director":
        class_map = {}
        for t in teachers:
            cn = t.get("class_name", "") or "미지정"
            if cn not in class_map:
                class_map[cn] = {"class_name": cn, "teachers": [], "children": []}
            class_map[cn]["teachers"].append(t)
        for c in children:
            cn = c.get("class_name", "") or "미지정"
            if cn not in class_map:
                class_map[cn] = {"class_name": cn, "teachers": [], "children": []}
            class_map[cn]["children"].append(c)
        # 미지정 그룹은 마지막으로
        for cn in sorted(class_map.keys(), key=lambda x: (x == "미지정", x)):
            classes.append(class_map[cn])

    wiz.response.status(200, role=role, teachers=teachers, children=children, classes=classes)

def delete_teacher():
    role = wiz.session.get("role")
    if role != "director":
        wiz.response.status(403, message="원장만 삭제할 수 있습니다.")

    teacher_id = wiz.request.query("teacher_id", True)
    teacher_id = int(teacher_id)

    server_id = wiz.session.get("server_id") or wiz.session.get("join_server_id")

    try:
        member = ServerMembers.select().where(
            ServerMembers.server_id == int(server_id),
            ServerMembers.user_id == teacher_id
        ).first()
        if not member:
            wiz.response.status(404, message="해당 교사를 찾을 수 없습니다.")
    except Exception as e:
        wiz.response.status(500, message=str(e))

    try:
        user = Users.select().where(Users.id == teacher_id).first()
        if not user or user.role != "teacher":
            wiz.response.status(400, message="교사가 아닙니다.")
    except Exception as e:
        wiz.response.status(500, message=str(e))

    try:
        ServerMembers.delete().where(
            ServerMembers.server_id == int(server_id),
            ServerMembers.user_id == teacher_id
        ).execute()
    except Exception:
        pass

    try:
        Users.delete().where(Users.id == teacher_id).execute()
    except Exception as e:
        wiz.response.status(500, message=str(e))

    wiz.response.status(200, message="교사가 삭제되었습니다.")

def delete_child():
    role = wiz.session.get("role")
    if role != "director":
        wiz.response.status(403, message="원장만 삭제할 수 있습니다.")

    child_id = int(wiz.request.query("child_id", True))
    parent_id = int(wiz.request.query("parent_id", True))

    server_id = wiz.session.get("server_id") or wiz.session.get("join_server_id")

    try:
        member = ServerMembers.select().where(
            ServerMembers.server_id == int(server_id),
            ServerMembers.user_id == parent_id
        ).first()
        if not member:
            wiz.response.status(404, message="해당 학생을 찾을 수 없습니다.")
    except Exception as e:
        wiz.response.status(500, message=str(e))

    if child_id > 0:
        try:
            ChildAllergies.delete().where(ChildAllergies.child_id == child_id).execute()
        except Exception:
            pass
        try:
            Children.delete().where(Children.id == child_id).execute()
        except Exception:
            pass

    remaining = 0
    try:
        remaining = Children.select().where(Children.user_id == parent_id).count()
    except Exception:
        pass

    if remaining == 0:
        try:
            ServerMembers.delete().where(
                ServerMembers.server_id == int(server_id),
                ServerMembers.user_id == parent_id
            ).execute()
        except Exception:
            pass
        try:
            Users.delete().where(Users.id == parent_id).execute()
        except Exception:
            pass

    wiz.response.status(200, message="학생이 삭제되었습니다.")

def delete_class():
    role = wiz.session.get("role")
    if role != "director":
        wiz.response.status(403, message="원장만 삭제할 수 있습니다.")

    class_name = wiz.request.query("class_name", True)
    server_id = wiz.session.get("server_id") or wiz.session.get("join_server_id")

    if not server_id:
        wiz.response.status(400, message="서버 정보가 없습니다.")

    server_id = int(server_id)

    # 현재 서버 소속 사용자 ID 목록
    server_user_ids = []
    try:
        members = ServerMembers.select(ServerMembers.user_id).where(
            ServerMembers.server_id == server_id
        )
        server_user_ids = [m.user_id for m in members]
    except Exception as e:
        wiz.response.status(500, message=str(e))

    if not server_user_ids:
        wiz.response.status(200, message="삭제할 대상이 없습니다.")

    deleted_teachers = 0
    deleted_children = 0
    deleted_parents = 0

    # 1. 해당 반 교사 삭제
    errors = []
    try:
        teacher_rows = Users.select(Users.id).where(
            Users.id.in_(server_user_ids),
            Users.role == "teacher",
            Users.class_name == class_name
        )
        teacher_ids = [t.id for t in teacher_rows]
        if teacher_ids:
            ServerMembers.delete().where(
                ServerMembers.server_id == server_id,
                ServerMembers.user_id.in_(teacher_ids)
            ).execute()
            Users.delete().where(Users.id.in_(teacher_ids)).execute()
            deleted_teachers = len(teacher_ids)
    except Exception as e:
        errors.append("교사 삭제 오류: " + str(e))

    # 2. 해당 반 학부모 및 자녀 삭제
    try:
        parent_rows = Users.select(Users.id).where(
            Users.id.in_(server_user_ids),
            Users.role == "parent",
            Users.class_name == class_name
        )
        parent_ids = [p.id for p in parent_rows]

        for pid in parent_ids:
            # 자녀의 알레르기 정보 삭제
            child_rows = Children.select(Children.id).where(Children.user_id == pid)
            child_ids = [c.id for c in child_rows]
            if child_ids:
                ChildAllergies.delete().where(ChildAllergies.child_id.in_(child_ids)).execute()
                deleted_children += len(child_ids)
            # 자녀 삭제
            Children.delete().where(Children.user_id == pid).execute()

        if parent_ids:
            # 서버 멤버 삭제
            ServerMembers.delete().where(
                ServerMembers.server_id == server_id,
                ServerMembers.user_id.in_(parent_ids)
            ).execute()
            # 학부모 계정 삭제
            Users.delete().where(Users.id.in_(parent_ids)).execute()
            deleted_parents = len(parent_ids)
    except Exception as e:
        errors.append("학부모/자녀 삭제 오류: " + str(e))

    if errors:
        wiz.response.status(500, message="일부 삭제 중 오류 발생: " + " | ".join(errors))

    wiz.response.status(200,
        message=f"'{class_name}' 반이 삭제되었습니다. (교사 {deleted_teachers}명, 학생 {deleted_children}명, 학부모 {deleted_parents}명)",
        deleted_teachers=deleted_teachers,
        deleted_children=deleted_children,
        deleted_parents=deleted_parents
    )

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

def upload_child_photo():
    role = wiz.session.get("role")
    if role not in ['teacher', 'director']:
        wiz.response.status(403, message="권한이 없습니다.")

    child_id = wiz.request.query("child_id", True)
    child_id = int(child_id)

    file = wiz.request.file("photo")
    if not file or not file.filename:
        wiz.response.status(400, message="사진을 선택해주세요.")

    try:
        child = Children.select().where(Children.id == child_id).first()
    except Exception as e:
        wiz.response.status(400, message=str(e))

    if not child:
        wiz.response.status(400, message="해당 아이를 찾을 수 없습니다.")

    fs = wiz.project.fs("data", "profile_photos")
    safe_name = f"child_{child_id}_{int(datetime.datetime.now().timestamp())}.jpg"
    save_path = fs.abspath(safe_name)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    try:
        compressed = _compress_image(file.read())
        with open(save_path, 'wb') as wf:
            wf.write(compressed)
    except Exception as e:
        wiz.response.status(500, message=str(e))

    old_photo = child.profile_photo
    if old_photo:
        try:
            old_path = fs.abspath(old_photo)
            if os.path.isfile(old_path):
                os.remove(old_path)
        except Exception:
            pass

    try:
        Children.update(profile_photo=safe_name).where(Children.id == child_id).execute()
    except Exception as e:
        wiz.response.status(500, message=str(e))

    wiz.response.status(200, profile_photo=safe_name)
