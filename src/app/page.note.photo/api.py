import os
import datetime
import calendar
import threading
from PIL import Image
import io

Photos = wiz.model("db/childcheck/photos")
Notifications = wiz.model("db/childcheck/notifications")
Users = wiz.model("db/login_db/users")
ServerMembers = wiz.model("db/login_db/server_members")
push = wiz.model("push")
Children = wiz.model("db/childcheck/children")
ChildAllergies = wiz.model("db/childcheck/child_allergies")
PhotoComments = wiz.model("db/childcheck/photo_comments")

# Force utf8mb4 charset on DB connection for emoji support
try:
    PhotoComments._meta.database.execute_sql('SET NAMES utf8mb4')
except Exception:
    pass

MEAL_TYPES = ['오전간식', '점심식사', '오후간식']
MAX_IMAGE_WIDTH = 1200
JPEG_QUALITY = 85

def _compress_image(file_data, max_width=MAX_IMAGE_WIDTH, quality=JPEG_QUALITY):
    """이미지를 리사이즈하고 JPEG로 압축하여 bytes를 반환한다."""
    img = Image.open(io.BytesIO(file_data))
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')
    w, h = img.size
    if w > max_width:
        ratio = max_width / w
        img = img.resize((max_width, int(h * ratio)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=quality, optimize=True)
    return buf.getvalue()

def notify_server_parents(server_id, noti_type, title, message, link=""):
    try:
        parent_members = ServerMembers.select(ServerMembers.user_id).where(
            (ServerMembers.server_id == int(server_id)) & (ServerMembers.role == "parent")
        )
        parent_ids = [m.user_id for m in parent_members]
        if not parent_ids:
            return
        for pid in parent_ids:
            Notifications.create(
                user_id=pid,
                type=noti_type,
                title=title,
                message=message,
                link=link
            )
            try:
                push.send_to_user(pid, title, message, url=link or "/note", noti_type=noti_type)
            except Exception:
                pass
    except Exception:
        pass

def get_role():
    role = wiz.session.get("role")
    if not role:
        wiz.response.status(401, message="로그인이 필요합니다.")

    has_allergy = False
    if role == "parent":
        user_id = wiz.session.get("id")
        try:
            child_ids = [c.id for c in Children.select(Children.id).where(Children.user_id == int(user_id))]
            if child_ids:
                allergy_count = ChildAllergies.select().where(ChildAllergies.child_id.in_(child_ids)).count()
                has_allergy = allergy_count > 0
        except Exception:
            pass

    wiz.response.status(200, role=role, has_allergy=has_allergy, user_id=int(wiz.session.get("id", 0)))

def _build_days_response(photos_rows, year, month):
    photos = []
    for row in photos_rows:
        date_str = ""
        if row.photo_date:
            date_str = row.photo_date.strftime("%Y.%m.%d")
        photos.append({
            'id': row.id,
            'meal_type': row.meal_type or '',
            'photo_date': date_str,
            'photo_path': row.photo_path,
        })

    date_map = {}
    for p in photos:
        d = p['photo_date']
        if d not in date_map:
            date_map[d] = {}
        if p['meal_type']:
            date_map[d][p['meal_type']] = p

    days = []
    for date_str in sorted(date_map.keys(), reverse=True):
        slots = []
        for mt in MEAL_TYPES:
            photo = date_map[date_str].get(mt)
            slots.append({
                'meal_type': mt,
                'photo': photo
            })
        days.append({
            'date': date_str,
            'slots': slots
        })

    return days

def get_public_photos():
    role = wiz.session.get("role")
    if not role:
        wiz.response.status(401, message="로그인이 필요합니다.")

    server_id = wiz.session.get("server_id") or wiz.session.get("join_server_id")
    if not server_id:
        wiz.response.status(400, message="서버 정보가 없습니다.")

    year = int(wiz.request.query("year", datetime.date.today().year))
    month = int(wiz.request.query("month", datetime.date.today().month))

    first_day = datetime.date(year, month, 1)
    last_day_num = calendar.monthrange(year, month)[1]
    last_day = datetime.date(year, month, last_day_num)

    rows = []
    try:
        rows = Photos.select().where(
            (Photos.category == "공용") &
            (Photos.server_id == int(server_id)) &
            (Photos.photo_date >= first_day) &
            (Photos.photo_date <= last_day)
        ).order_by(Photos.photo_date.desc())
    except Exception:
        pass

    days = _build_days_response(rows, year, month)
    wiz.response.status(200, days=days)

def get_child_photos():
    role = wiz.session.get("role")
    if not role:
        wiz.response.status(401, message="로그인이 필요합니다.")

    server_id = wiz.session.get("server_id") or wiz.session.get("join_server_id")
    if not server_id:
        wiz.response.status(400, message="서버 정보가 없습니다.")

    if role == "parent":
        target_user_id = int(wiz.session.get("id"))
    else:
        target_user_id = int(wiz.request.query("target_user_id", True))

    year = int(wiz.request.query("year", datetime.date.today().year))
    month = int(wiz.request.query("month", datetime.date.today().month))

    first_day = datetime.date(year, month, 1)
    last_day_num = calendar.monthrange(year, month)[1]
    last_day = datetime.date(year, month, last_day_num)

    rows = []
    try:
        rows = Photos.select().where(
            (Photos.category == "아이") &
            (Photos.server_id == int(server_id)) &
            (Photos.target_user_id == target_user_id) &
            (Photos.photo_date >= first_day) &
            (Photos.photo_date <= last_day)
        ).order_by(Photos.photo_date.desc())
    except Exception:
        pass

    days = _build_days_response(rows, year, month)
    wiz.response.status(200, days=days)

def get_photos():
    role = wiz.session.get("role")
    if not role:
        wiz.response.status(401, message="로그인이 필요합니다.")

    server_id = wiz.session.get("server_id") or wiz.session.get("join_server_id")
    if not server_id:
        wiz.response.status(400, message="서버 정보가 없습니다.")

    category = wiz.request.query("category", "공용")
    target_user_id = int(wiz.request.query("target_user_id", 0))

    photos = []
    try:
        conditions = (Photos.category == category) & (Photos.server_id == int(server_id))

        if category == "아이":
            if role == "parent":
                user_id = wiz.session.get("id")
                conditions = conditions & (Photos.target_user_id == int(user_id))
            elif target_user_id > 0:
                conditions = conditions & (Photos.target_user_id == target_user_id)

        rows = Photos.select().where(conditions).order_by(Photos.created_at.desc())
        for row in rows:
            created_str = ""
            if row.created_at:
                created_str = row.created_at.strftime("%Y년 %m월 %d일")
            photos.append({
                'id': row.id,
                'category': row.category,
                'title': row.title or '',
                'photo_path': row.photo_path,
                'created_at': created_str,
            })
    except Exception:
        pass

    wiz.response.status(200, photos=photos)

def get_children_list():
    role = wiz.session.get("role")
    if role not in ['teacher', 'director']:
        wiz.response.status(403, message="권한이 없습니다.")

    user_id = wiz.session.get("id")
    server_id = wiz.session.get("server_id") or wiz.session.get("join_server_id")
    if not server_id:
        wiz.response.status(400, message="서버 정보가 없습니다.")

    server_user_ids = []
    try:
        members = ServerMembers.select(ServerMembers.user_id).where(ServerMembers.server_id == int(server_id))
        server_user_ids = [m.user_id for m in members]
    except Exception:
        pass

    allergy_user_ids = set()
    try:
        allergy_child_ids = [a.child_id for a in ChildAllergies.select(ChildAllergies.child_id).distinct()]
        if allergy_child_ids:
            allergy_children = Children.select(Children.user_id).where(Children.id.in_(allergy_child_ids))
            allergy_user_ids = set(c.user_id for c in allergy_children)
    except Exception:
        pass

    children = []
    teacher_class = ""

    if role == "teacher":
        try:
            me = Users.select(Users.class_name).where(Users.id == int(user_id)).first()
            if me and me.class_name:
                teacher_class = me.class_name.strip()
        except Exception:
            pass

    if server_user_ids:
        try:
            query = Users.select(Users.id, Users.nickname, Users.child_name, Users.class_name).where(
                Users.id.in_(server_user_ids),
                Users.role == "parent"
            )
            if role == "teacher" and teacher_class:
                query = query.where(Users.class_name == teacher_class)

            for p in query:
                if p.id not in allergy_user_ids:
                    continue
                child_name = p.child_name or p.nickname or "이름 없음"
                children.append({
                    'user_id': p.id,
                    'child_name': child_name,
                    'nickname': p.nickname or "",
                    'class_name': (p.class_name or "").strip()
                })
        except Exception:
            pass

    wiz.response.status(200, children=children)

def serve_photo():
    filename = wiz.request.query("filename", True)
    if ".." in filename or "/" in filename:
        wiz.response.abort(400)
    fs = wiz.project.fs("data", "photos")
    filepath = fs.abspath(filename)
    if not os.path.isfile(filepath):
        name, ext = os.path.splitext(filename)
        alt = name + ('.jpg' if ext == '.jpeg' else '.jpeg')
        alt_path = fs.abspath(alt)
        if os.path.isfile(alt_path):
            filepath = alt_path
        else:
            wiz.response.abort(404)

    flask = wiz.response._flask
    resp = flask.send_file(filepath, mimetype='image/jpeg')
    resp.headers['Cache-Control'] = 'public, max-age=604800, immutable'
    mtime = str(int(os.path.getmtime(filepath)))
    resp.headers['ETag'] = f'"{mtime}"'
    wiz.response.response(resp)

def upload_photo():
    role = wiz.session.get("role")
    if role not in ['teacher', 'director']:
        wiz.response.status(403, message="권한이 없습니다.")

    user_id = wiz.session.get("id")
    server_id = wiz.session.get("server_id") or wiz.session.get("join_server_id")
    if not server_id:
        wiz.response.status(400, message="서버 정보가 없습니다.")

    category = wiz.request.query("category", "공용")
    title = wiz.request.query("title", "")
    target_user_id = int(wiz.request.query("target_user_id", 0))
    meal_type = wiz.request.query("meal_type", "")
    photo_date_str = wiz.request.query("photo_date", "")

    file = wiz.request.file("photo")
    if not file or not file.filename:
        wiz.response.status(400, message="사진을 선택해주세요.")

    fs = wiz.project.fs("data", "photos")
    safe_name = str(datetime.datetime.now().timestamp()).replace(".", "") + ".jpg"
    save_path = fs.abspath(safe_name)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    compressed = _compress_image(file.read())
    with open(save_path, 'wb') as wf:
        wf.write(compressed)

    photo_date = None
    if photo_date_str:
        try:
            photo_date = datetime.datetime.strptime(photo_date_str, "%Y.%m.%d").date()
        except Exception:
            try:
                photo_date = datetime.datetime.strptime(photo_date_str, "%Y-%m-%d").date()
            except Exception:
                pass

    # 공용 카테고리에서 같은 날짜+meal_type 사진이 이미 존재하면 교체
    if category == "공용" and meal_type and photo_date:
        try:
            existing = Photos.select().where(
                (Photos.category == "공용") &
                (Photos.server_id == int(server_id)) &
                (Photos.meal_type == meal_type) &
                (Photos.photo_date == photo_date)
            ).first()
            if existing:
                old_path = existing.photo_path
                Photos.delete().where(Photos.id == existing.id).execute()
                try:
                    old_file = fs.abspath(old_path)
                    if os.path.isfile(old_file):
                        os.remove(old_file)
                except Exception:
                    pass
        except Exception:
            pass

    # 아이 카테고리에서 같은 날짜+meal_type+target_user_id 사진이 있으면 교체
    if category == "아이" and meal_type and photo_date and target_user_id > 0:
        try:
            existing = Photos.select().where(
                (Photos.category == "아이") &
                (Photos.server_id == int(server_id)) &
                (Photos.target_user_id == target_user_id) &
                (Photos.meal_type == meal_type) &
                (Photos.photo_date == photo_date)
            ).first()
            if existing:
                old_path = existing.photo_path
                Photos.delete().where(Photos.id == existing.id).execute()
                try:
                    old_file = fs.abspath(old_path)
                    if os.path.isfile(old_file):
                        os.remove(old_file)
                except Exception:
                    pass
        except Exception:
            pass

    try:
        Photos.create(
            category=category,
            server_id=int(server_id),
            target_user_id=target_user_id,
            title=title,
            meal_type=meal_type if meal_type else None,
            photo_date=photo_date,
            photo_path=safe_name,
            created_by=user_id
        )
    except Exception as e:
        wiz.response.status(500, message=str(e))

    # 알림을 별도 스레드로 분리하여 업로드 응답 즉시 반환
    _server_id = int(server_id)
    _category = category
    _meal_type = meal_type
    _title = title
    _target_user_id = target_user_id

    def _send_notification():
        try:
            if _category == "공용":
                noti_title = "공용 식단표 사진 업로드"
                if _meal_type:
                    noti_title = _meal_type + " 사진 업로드"
                notify_server_parents(_server_id, "photo", noti_title, _title or "새 사진이 등록되었습니다.", "/note/photo")
            elif _target_user_id > 0:
                Notifications.create(
                    user_id=_target_user_id,
                    type="photo",
                    title="아이 맞춤 식단 업로드",
                    message=_title or "새 사진이 등록되었습니다.",
                    link="/note/photo"
                )
                try:
                    push.send_to_user(_target_user_id, "아이 맞춤 식단 업로드", _title or "새 사진이 등록되었습니다.", url="/note/photo", noti_type="photo")
                except Exception:
                    pass
        except Exception:
            pass

    threading.Thread(target=_send_notification, daemon=True).start()

    wiz.response.status(200)

def delete_photo():
    role = wiz.session.get("role")
    if role not in ['teacher', 'director']:
        wiz.response.status(403, message="권한이 없습니다.")

    photo_id = int(wiz.request.query("id", True))

    try:
        photo = Photos.select().where(Photos.id == photo_id).first()
        if photo:
            fs = wiz.project.fs("data", "photos")
            try:
                old_file = fs.abspath(photo.photo_path)
                if os.path.isfile(old_file):
                    os.remove(old_file)
            except Exception:
                pass
            Photos.delete().where(Photos.id == photo_id).execute()
    except Exception as e:
        wiz.response.status(500, message=str(e))

    wiz.response.status(200)

def delete_date_photos():
    role = wiz.session.get("role")
    if role not in ['teacher', 'director']:
        wiz.response.status(403, message="권한이 없습니다.")

    server_id = wiz.session.get("server_id") or wiz.session.get("join_server_id")
    if not server_id:
        wiz.response.status(400, message="서버 정보가 없습니다.")

    date_str = wiz.request.query("date", True)
    category = wiz.request.query("category", "공용")
    target_user_id = int(wiz.request.query("target_user_id", 0))

    photo_date = None
    try:
        photo_date = datetime.datetime.strptime(date_str, "%Y.%m.%d").date()
    except Exception:
        try:
            photo_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception:
            wiz.response.status(400, message="잘못된 날짜 형식입니다.")

    conditions = (
        (Photos.category == category) &
        (Photos.server_id == int(server_id)) &
        (Photos.photo_date == photo_date)
    )
    if category == "아이" and target_user_id > 0:
        conditions = conditions & (Photos.target_user_id == target_user_id)

    fs = wiz.project.fs("data", "photos")
    try:
        rows = Photos.select().where(conditions)
        for row in rows:
            try:
                old_file = fs.abspath(row.photo_path)
                if os.path.isfile(old_file):
                    os.remove(old_file)
            except Exception:
                pass
        Photos.delete().where(conditions).execute()
    except Exception as e:
        wiz.response.status(500, message=str(e))

    wiz.response.status(200)

def get_comments():
    role = wiz.session.get("role")
    if not role:
        wiz.response.status(401, message="로그인이 필요합니다.")

    photo_id = int(wiz.request.query("photo_id", True))

    comments = []
    try:
        rows = PhotoComments.select().where(
            PhotoComments.photo_id == photo_id
        ).order_by(PhotoComments.created_at.asc())

        user_ids = list(set(r.user_id for r in rows))
        nickname_map = {}
        if user_ids:
            for u in Users.select(Users.id, Users.nickname).where(Users.id.in_(user_ids)):
                nickname_map[u.id] = u.nickname or "익명"

        for row in rows:
            created_str = ""
            if row.created_at:
                created_str = row.created_at.strftime("%m/%d %H:%M")
            comments.append({
                'id': row.id,
                'user_id': row.user_id,
                'nickname': nickname_map.get(row.user_id, "익명"),
                'content': row.content,
                'created_at': created_str
            })
    except Exception as e:
        wiz.response.status(500, message=str(e))

    wiz.response.status(200, comments=comments)

def add_comment():
    role = wiz.session.get("role")
    if not role:
        wiz.response.status(401, message="로그인이 필요합니다.")

    user_id = wiz.session.get("id")
    if not user_id:
        wiz.response.status(401, message="로그인이 필요합니다.")

    photo_id = int(wiz.request.query("photo_id", True))
    content = wiz.request.query("content", True)

    if len(content) > 50:
        content = content[:50]

    try:
        PhotoComments.create(
            photo_id=photo_id,
            user_id=int(user_id),
            content=content
        )
    except Exception as e:
        wiz.response.status(500, message=str(e))

    wiz.response.status(200)

def delete_comment():
    role = wiz.session.get("role")
    if not role:
        wiz.response.status(401, message="로그인이 필요합니다.")

    user_id = wiz.session.get("id")
    if not user_id:
        wiz.response.status(401, message="로그인이 필요합니다.")

    comment_id = int(wiz.request.query("comment_id", True))

    try:
        comment = PhotoComments.get_or_none(PhotoComments.id == comment_id)
    except Exception as e:
        wiz.response.status(500, message=str(e))

    if not comment:
        wiz.response.status(404, message="댓글을 찾을 수 없습니다.")

    if role == "parent" and comment.user_id != int(user_id):
        wiz.response.status(403, message="본인 댓글만 삭제할 수 있습니다.")

    try:
        PhotoComments.delete().where(PhotoComments.id == comment_id).execute()
    except Exception as e:
        wiz.response.status(500, message=str(e))

    wiz.response.status(200)
