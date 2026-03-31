import json
import re
from datetime import datetime, timedelta

Notifications = wiz.model("db/childcheck/notifications")
Users = wiz.model("db/login_db/users")
Meals = wiz.model("db/childcheck/meals")
Children = wiz.model("db/childcheck/children")
ChildAllergies = wiz.model("db/childcheck/child_allergies")
AllergyCategories = wiz.model("db/childcheck/allergy_categories")
ServerMembers = wiz.model("db/login_db/server_members")

ALLERGY_TYPE_TO_NUMBERS = {
    '계란': [1], '난류': [1],
    '우유': [2],
    '메밀': [3],
    '땅콩': [4],
    '대두': [5],
    '밀': [6],
    '고등어': [7],
    '게': [8],
    '새우': [9],
    '돼지고기': [10],
    '복숭아': [11],
    '토마토': [12],
    '아황산류': [13],
    '호두': [14],
    '닭고기': [15],
    '쇠고기': [16],
    '오징어': [17],
    '조개류': [18],
    '잣': [19]
}

KEYWORD_ALIASES = {
    '돼지고기': ['돼지'],
    '닭고기': ['닭'],
    '쇠고기': ['소고기', '쇠'],
    '소고기': ['쇠고기', '쇠'],
}

def _get_server_id():
    server_id = wiz.session.get("join_server_id")
    if not server_id:
        server_id = wiz.session.get("server_id")
    if not server_id:
        wiz.response.status(401, message="서버 미선택")
    return int(server_id)

def _keyword_in_content(keyword, content):
    if keyword in content:
        return True
    for alias in KEYWORD_ALIASES.get(keyword, []):
        if alias in content:
            return True
    return False

def _build_caution_food_map():
    categories = AllergyCategories.select()
    food_map = {}
    cat_list = []
    for cat in categories:
        try:
            numbers = json.loads(cat.allergy_numbers) if cat.allergy_numbers else []
        except Exception:
            numbers = []
        raw_foods = (cat.caution_foods or '').replace('(', ',').replace(')', ',')
        foods = [f.strip() for f in raw_foods.split(',') if f.strip()]
        cat_list.append({
            'category_name': cat.category_name,
            'allergy_numbers': numbers,
            'substitute_foods': cat.substitute_foods or '',
            'caution_foods': foods
        })
        for food in foods:
            food_map[food] = {
                'category_name': cat.category_name,
                'allergy_numbers': numbers,
                'substitute_foods': cat.substitute_foods or ''
            }
    return food_map, cat_list

def get_role():
    user_id = wiz.session.get("id")
    role = ""
    if user_id:
        try:
            user = Users.select(Users.role).where(Users.id == user_id).first()
            if user:
                role = user.role or ""
        except Exception:
            pass
    wiz.response.status(200, role=role)

def get_unread_count():
    user_id = wiz.session.get("id")
    if not user_id:
        wiz.response.status(200, count=0)
    try:
        count = Notifications.select().where(
            (Notifications.user_id == user_id) & (Notifications.is_read == False)
        ).count()
    except Exception:
        count = 0
    wiz.response.status(200, count=count)

def get_notifications():
    user_id = wiz.session.get("id")
    if not user_id:
        wiz.response.status(200, notifications=[])
    try:
        rows = Notifications.select().where(
            Notifications.user_id == user_id
        ).order_by(Notifications.created_at.desc()).limit(20)
        result = []
        for r in rows:
            result.append({
                "id": r.id,
                "type": r.type,
                "title": r.title,
                "message": r.message or "",
                "link": r.link or "",
                "is_read": r.is_read,
                "created_at": str(r.created_at)
            })
    except Exception:
        result = []
    wiz.response.status(200, notifications=result)

def read_notification():
    noti_id = wiz.request.query("id", True)
    user_id = wiz.session.get("id")
    if not user_id:
        wiz.response.status(401)
    try:
        Notifications.update(is_read=True).where(
            (Notifications.id == int(noti_id)) & (Notifications.user_id == user_id)
        ).execute()
    except Exception as e:
        wiz.response.status(500, message=str(e))
    wiz.response.status(200)

def read_all():
    user_id = wiz.session.get("id")
    if not user_id:
        wiz.response.status(401)
    try:
        Notifications.update(is_read=True).where(
            (Notifications.user_id == user_id) & (Notifications.is_read == False)
        ).execute()
    except Exception as e:
        wiz.response.status(500, message=str(e))
    wiz.response.status(200)

def leave_server():
    wiz.session.clear()
    wiz.response.status(200)

def logout():
    join_server_id = wiz.session.get("join_server_id")
    join_server_name = wiz.session.get("join_server_name")
    wiz.session.clear()
    if join_server_id:
        wiz.session.set(join_server_id=join_server_id)
    if join_server_name:
        wiz.session.set(join_server_name=join_server_name)
    wiz.response.status(200)

def get_weekly_allergy():
    server_id = _get_server_id()

    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    start_date = monday.strftime('%Y-%m-%d')
    end_date = sunday.strftime('%Y-%m-%d')

    meals_query = Meals.select().where(
        (Meals.server_id == server_id) &
        (Meals.meal_date >= start_date) &
        (Meals.meal_date <= end_date)
    )

    all_meal_numbers = set()
    all_meal_content = ""
    all_dishes = []
    all_dish_allergy_maps = []  # 각 meal의 dish_allergies 매핑
    for m in meals_query:
        try:
            nums = json.loads(m.allergy_numbers) if m.allergy_numbers else []
            all_meal_numbers.update(nums)
        except Exception:
            pass
        content = m.content or ""
        all_meal_content += " " + content
        clean_content = re.sub(r'\{\{green:(.*?)\}\}', r'\1', content)
        for d in re.split(r'[,\n/]', clean_content):
            d = re.sub(r'[\u2460-\u2473\u3251-\u325f\d.]+$', '', d.strip()).strip()
            if d and d not in all_dishes:
                all_dishes.append(d)
        # dish_allergies 수집
        if m.dish_allergies:
            try:
                da_map = json.loads(m.dish_allergies)
                if da_map:
                    all_dish_allergy_maps.append(da_map)
            except Exception:
                pass
    has_dish_allergy_data = bool(all_dish_allergy_maps)

    members = ServerMembers.select().where(
        (ServerMembers.server_id == server_id) &
        (ServerMembers.role == 'parent')
    )
    parent_ids = [m.user_id for m in members]

    if not parent_ids:
        wiz.response.status(200, alerts=[], week_start=start_date, week_end=end_date)

    children_query = Children.select().where(Children.user_id.in_(parent_ids))
    child_map = {c.id: c for c in children_query}
    child_ids = list(child_map.keys())

    if not child_ids:
        wiz.response.status(200, alerts=[], week_start=start_date, week_end=end_date)

    allergies = ChildAllergies.select().where(ChildAllergies.child_id.in_(child_ids))
    caution_food_map, _ = _build_caution_food_map()

    raw_alerts = []

    for allergy in allergies:
        child = child_map.get(allergy.child_id)
        if not child:
            continue

        if allergy.allergy_type == '기타' and allergy.other_detail:
            keywords = [kw.strip() for kw in allergy.other_detail.replace('/', ',').split(',') if kw.strip()]
            for keyword in keywords:
                matched_foods = []
                alert_type = '기타 알레르기'
                detail = keyword

                if keyword in caution_food_map:
                    alert_type = caution_food_map[keyword]['category_name']

                # 키워드가 포함된 실제 식단명 찾기
                for dish in all_dishes:
                    if _keyword_in_content(keyword, dish):
                        if dish not in matched_foods:
                            matched_foods.append(dish)

                if matched_foods:
                    raw_alerts.append({
                        'child_name': child.name,
                        'child_id': child.id,
                        'allergy_type': alert_type,
                        'detail': detail,
                        'matched_foods': matched_foods,
                        'is_severe': bool(allergy.is_severe),
                    })
        else:
            allergy_nums = set(ALLERGY_TYPE_TO_NUMBERS.get(allergy.allergy_type, []))
            if not allergy_nums:
                continue

            if allergy_nums & all_meal_numbers:
                matched_foods = []

                if has_dish_allergy_data:
                    # dish_allergies로 정확한 매칭
                    for da_map in all_dish_allergy_maps:
                        for dish_name, dish_nums in da_map.items():
                            clean_dish = re.sub(r'\{\{green:(.*?)\}\}', r'\1', dish_name)
                            if set(dish_nums) & allergy_nums and clean_dish not in matched_foods:
                                matched_foods.append(clean_dish)
                else:
                    # fallback: 키워드 매칭
                    for food, cat_info in caution_food_map.items():
                        if set(cat_info['allergy_numbers']) & allergy_nums:
                            for dish in all_dishes:
                                if _keyword_in_content(food, dish) and dish not in matched_foods:
                                    matched_foods.append(dish)

                raw_alerts.append({
                    'child_name': child.name,
                    'child_id': child.id,
                    'allergy_type': allergy.allergy_type + ' 알레르기',
                    'detail': '',
                    'matched_foods': matched_foods,
                    'is_severe': bool(allergy.is_severe),
                })

    # 아이별 그룹핑
    grouped = {}
    for alert in raw_alerts:
        cid = alert['child_id']
        if cid not in grouped:
            grouped[cid] = {
                'child_name': alert['child_name'],
                'child_id': cid,
                'is_severe': False,
                'allergies': [],
                'matched_foods': []
            }
        label = alert['allergy_type']
        if alert['detail']:
            label += '(' + alert['detail'] + ')'
        grouped[cid]['allergies'].append(label)
        for food in alert.get('matched_foods', []):
            if food not in grouped[cid]['matched_foods']:
                grouped[cid]['matched_foods'].append(food)
        if alert['is_severe']:
            grouped[cid]['is_severe'] = True

    alerts = list(grouped.values())
    wiz.response.status(200, alerts=alerts, week_start=start_date, week_end=end_date)
