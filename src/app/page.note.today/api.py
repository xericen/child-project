# pyright: reportUndefinedVariable=false, reportMissingImports=false
import datetime
import json

Meals = wiz.model("db/childcheck/meals")
Children = wiz.model("db/childcheck/children")
ChildAllergies = wiz.model("db/childcheck/child_allergies")
AllergyCategories = wiz.model("db/childcheck/allergy_categories")
ServerMembers = wiz.model("db/login_db/server_members")
Users = wiz.model("db/login_db/users")

KST = datetime.timezone(datetime.timedelta(hours=9))

ALLERGY_MAP = {
    1: '난류', 2: '우유', 3: '메밀', 4: '땅콩', 5: '대두',
    6: '밀', 7: '고등어', 8: '게', 9: '새우', 10: '돼지고기',
    11: '복숭아', 12: '토마토', 13: '아황산류', 14: '호두',
    15: '닭고기', 16: '소고기', 17: '오징어', 18: '조개류', 19: '잣'
}

ALLERGY_TYPE_TO_NUMBERS = {
    '계란': [1], '우유': [2], '메밀': [3], '땅콩': [4], '대두': [5],
    '밀': [6], '고등어': [7], '게': [8], '새우': [9], '돼지고기': [10],
    '복숭아': [11], '토마토': [12], '아황산류': [13], '호두': [14],
    '닭고기': [15], '소고기': [16], '쇠고기': [16], '오징어': [17], '조개류': [18],
    '잣': [19], '난류': [1],
}

# 연령별 어린이집 제공분 목표 영양소 — nutrition_api.py 공유 상수에서 변환
def _build_daycare_targets():
    """nutrition_api.py의 DAYCARE_TARGETS(nested)를 flat dict로 변환"""
    _api = wiz.model("nutrition_api")
    _src = _api.DAYCARE_TARGETS
    # nutrition_api 키(carbohydrate) → api.py 표시 키(carbs) 변환
    key_map = {'carbohydrate': 'carbs'}
    targets = {}
    for age_label, nutrients in _src.items():
        age_key = age_label.replace('세', '')  # '1~2세' → '1~2'
        flat = {}
        for k, v in nutrients.items():
            display_key = key_map.get(k, k)
            flat[display_key] = v['value']
        targets[age_key] = flat
    return targets

DAYCARE_TARGETS = _build_daycare_targets()
DAYCARE_TARGET = DAYCARE_TARGETS['1~2']  # 키 목록용 기본값

import re

KEYWORD_ALIASES = {
    '돼지고기': ['돼지', '돈까스', '돈가스', '돈', '삼겹', '햄', '소시지', '베이컨', '만두', '교자', '탕수육', '제육', '수육', '족발', '보쌈'],
    '닭고기': ['닭', '치킨', '닭볶음', '닭갈비', '닭강정', '너겟'],
    '쇠고기': ['소고기', '쇠', '불고기', '갈비', '소갈비', '육개장', '설렁탕', '곰탕'],
    '소고기': ['쇠고기', '쇠', '불고기', '갈비', '소갈비', '육개장', '설렁탕', '곰탕'],
    '난류': ['계란', '달걀', '에그', '오믈렛', '스크램블', '후라이'],
    '우유': ['밀크', '크림', '치즈', '요거트', '요구르트', '버터'],
    '대두': ['두부', '콩', '된장', '간장', '두유', '콩나물'],
    '밀': ['빵', '면', '국수', '파스타', '라면', '우동', '수제비', '만두피', '부침개', '전'],
    '새우': ['새우깡', '젓갈'],
    '땅콩': ['피넛'],
}

def _keyword_in_content(keyword, content):
    if keyword in content:
        return True
    for alias in KEYWORD_ALIASES.get(keyword, []):
        if alias in content:
            return True
    return False

_ai_allergy_cache = {}

def _ai_map_other_allergy(other_detail):
    """기타 알레르기 키워드가 표준 19종 중 어디에 해당하는지 AI로 분석 (캐시 적용)."""
    if not other_detail or not other_detail.strip():
        return []
    key = other_detail.strip()
    if key in _ai_allergy_cache:
        return _ai_allergy_cache[key]
    allergy_list = ", ".join([f"{v}({k}번)" for k, v in ALLERGY_MAP.items()])
    try:
        gemini = wiz.model("gemini")
        prompt = f"""아이의 알레르기가 "{key}"입니다.
표준 19종 알레르기: {allergy_list}
이 알레르기가 표준 19종 중 어떤 항목에 해당하는지 번호만 반환해주세요.
해당하는 게 없으면 빈 배열을 반환하세요.
JSON 형식: {{"numbers": [10]}}"""
        result = gemini.ask_json(prompt, system_instruction="알레르기 전문가입니다. JSON만 응답하세요.")
        if isinstance(result, dict) and 'numbers' in result:
            nums = [int(n) for n in result['numbers'] if isinstance(n, (int, float)) and 1 <= int(n) <= 19]
            _ai_allergy_cache[key] = nums
            return nums
    except Exception:
        pass
    _ai_allergy_cache[key] = []
    return []

def _get_daycare_target(age):
    """자녀 나이 기반 DAYCARE_TARGET 반환"""
    if age >= 3:
        return DAYCARE_TARGETS['3~5']
    return DAYCARE_TARGETS['1~2']

# 연령별 연결 메뉴 쌍 (1~2세 메뉴, 3~5세 메뉴) — nutrition_api.AGE_MENU_PAIRS와 동기화
_AGE_MENU_PAIRS = [('백김치', '배추김치')]
_GREEN_RE = re.compile(r'\{\{green:.*?\}\}')

def _adapt_content_for_age(content, age_group):
    """식단 content를 해당 연령의 메뉴만 표시하도록 변환.
    - 연결 메뉴(백김치배추김치) → 연령에 맞는 것만
    - green 마커 → 1~2세는 green이 실제메뉴, 3~5세는 원본이 실제메뉴"""
    if not content:
        return content
    # 1. 연결 메뉴 분리
    for young, old in _AGE_MENU_PAIRS:
        young_pat = r'\s*'.join(re.escape(ch) for ch in young)
        old_pat = r'\s*'.join(re.escape(ch) for ch in old)
        pattern = young_pat + r'\s*' + old_pat
        content = re.sub(pattern, young if age_group == '1~2세' else old, content)
    # 2. green 마커 처리
    lines = content.split('\n')
    result = []
    if age_group == '1~2세':
        for line in lines:
            if '{{green:' in line:
                # green 텍스트 추출
                green_texts = [m.group(1) for m in re.finditer(r'\{\{green:(.*?)\}\}', line)]
                remainder = _GREEN_RE.sub('', line).strip()
                # 직전 항목(3~5세용) 제거
                if result:
                    result.pop()
                # green 텍스트 추가
                for gt in green_texts:
                    gt = gt.strip()
                    if gt and gt not in ('/', '-'):
                        result.append(gt)
                # 같은줄 공통 텍스트 추가
                if remainder:
                    result.append(remainder)
            else:
                result.append(line)
    else:
        for line in lines:
            if '{{green:' in line:
                remainder = _GREEN_RE.sub('', line).strip()
                if remainder:
                    result.append(remainder)
                # green 아이템 제거 (3~5세는 원본 사용)
            else:
                result.append(line)
    return '\n'.join(result)

NUTRIENT_LABEL_MAP = {
    'calories': ('칼로리', 'kcal'),
    'protein': ('단백질', 'g'),
    'fat': ('지방', 'g'),
    'carbs': ('탄수화물', 'g'),
    'calcium': ('칼슘', 'mg'),
    'iron': ('철분', 'mg'),
}

def _get_server_id():
    server_id = wiz.session.get("server_id") or wiz.session.get("join_server_id")
    if not server_id:
        wiz.response.status(401, message="서버 정보가 없습니다.")
    return int(server_id)

def _build_caution_food_map():
    mapping = {}
    try:
        cats = AllergyCategories.select()
        for cat in cats:
            nums = json.loads(cat.allergy_numbers) if isinstance(cat.allergy_numbers, str) else cat.allergy_numbers
            foods = [f.strip() for f in cat.caution_foods.replace('(', ',').replace(')', ',').split(',') if f.strip()]
            for food in foods:
                if food not in mapping:
                    mapping[food] = nums
    except Exception:
        pass
    return mapping

def _get_today_meals(server_id):
    today = datetime.datetime.now(KST).date()
    meals = []
    try:
        rows = Meals.select().where(
            (Meals.server_id == server_id) & (Meals.meal_date == today)
        ).order_by(Meals.id)
        for row in rows:
            allergy_nums = []
            if row.allergy_numbers:
                try:
                    allergy_nums = json.loads(row.allergy_numbers)
                except Exception:
                    pass
            kcal_val = None
            protein_val = None
            kcal_35_val = None
            protein_35_val = None
            try:
                kcal_val = row.kcal
                protein_val = row.protein
                kcal_35_val = row.kcal_35
                protein_35_val = row.protein_35
            except Exception:
                pass
            meals.append({
                'meal_type': row.meal_type,
                'content': row.content or '',
                'allergy_numbers': allergy_nums,
                'dish_allergies': json.loads(row.dish_allergies) if row.dish_allergies else {},
                'kcal': kcal_val,
                'protein': protein_val,
                'kcal_35': kcal_35_val,
                'protein_35': protein_35_val
            })
    except Exception:
        pass
    return meals

def _extract_warning_menu_name(content):
    if not content:
        return '알 수 없는 메뉴'
    normalized = content.replace('<br>', '\n')
    for raw_line in normalized.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        cleaned = line
        while '{{green:' in cleaned and '}}' in cleaned:
            start = cleaned.find('{{green:')
            end = cleaned.find('}}', start)
            if end == -1:
                break
            cleaned = (cleaned[:start] + cleaned[end + 2:]).strip()
        if cleaned:
            return cleaned
    return '알 수 없는 메뉴'

def _get_server_children(server_id):
    parent_ids = [sm.user_id for sm in ServerMembers.select(ServerMembers.user_id).where(
        (ServerMembers.server_id == server_id) & (ServerMembers.role == "parent")
    )]
    if not parent_ids:
        return {}
    child_name_map = {}
    for c in Children.select().where(Children.user_id.in_(parent_ids)):
        child_name_map[c.id] = c.name
    return child_name_map

def _get_my_children_info(user_id):
    children_info = []
    try:
        children = list(Children.select().where(Children.user_id == int(user_id)))
        today = datetime.datetime.now(KST).date()
        for child in children:
            age = 0
            if child.birthdate:
                age = today.year - child.birthdate.year
                if (today.month, today.day) < (child.birthdate.month, child.birthdate.day):
                    age -= 1

            allergies = []
            try:
                for ca in ChildAllergies.select().where(ChildAllergies.child_id == child.id):
                    atype = ca.allergy_type
                    if atype == '기타' and ca.other_detail:
                        atype = f"기타({ca.other_detail})"
                    allergies.append(atype)
            except Exception:
                pass

            children_info.append({
                'name': child.name,
                'age': age,
                'allergies': allergies
            })
    except Exception:
        pass
    return children_info

def _to_display_nutrients(api_nutrients, ratio=1.0):
    """nutrition_api 키 → 프론트엔드 표시용 키로 변환 + 비율 보정"""
    return {
        'calories': round((api_nutrients.get('calories', 0)) * ratio, 1),
        'protein': round((api_nutrients.get('protein', 0)) * ratio, 1),
        'fat': round((api_nutrients.get('fat', 0)) * ratio, 1),
        'carbs': round((api_nutrients.get('carbohydrate', 0)) * ratio, 1),
        'calcium': round((api_nutrients.get('calcium', 0)) * ratio, 1),
        'iron': round((api_nutrients.get('iron', 0)) * ratio, 1),
    }

def get_today_menu():
    role = wiz.session.get("role")
    if not role:
        wiz.response.status(401, message="로그인이 필요합니다.")

    server_id = _get_server_id()
    meals = _get_today_meals(server_id)

    morning_snack = ""
    lunch = ""
    afternoon_snack = ""
    meal_allergy = {}
    meal_content_map = {}
    meal_dish_allergy_map = {}
    for m in meals:
        if m['meal_type'] == '오전간식':
            morning_snack = m['content']
            meal_allergy['오전간식'] = m['allergy_numbers']
            meal_content_map['오전간식'] = m['content']
            meal_dish_allergy_map['오전간식'] = m.get('dish_allergies', {})
        elif m['meal_type'] == '점심':
            lunch = m['content']
            meal_allergy['점심'] = m['allergy_numbers']
            meal_content_map['점심'] = m['content']
            meal_dish_allergy_map['점심'] = m.get('dish_allergies', {})
        elif m['meal_type'] == '오후간식':
            afternoon_snack = m['content']
            meal_allergy['오후간식'] = m['allergy_numbers']
            meal_content_map['오후간식'] = m['content']
            meal_dish_allergy_map['오후간식'] = m.get('dish_allergies', {})

    # 자녀 알레르기 매칭 (모든 역할) — 단일 패스로 번호+키워드 수집
    allergy_warnings = {}
    child_allergy_nums = set()
    other_keywords = []

    def _collect_allergy_data(allergy_rows):
        """ChildAllergies 행에서 번호와 기타 키워드를 한 번에 수집"""
        for ca in allergy_rows:
            if ca.allergy_type == '기타' and ca.other_detail:
                detail = ca.other_detail.strip()
                # 기타 키워드 수집
                for kw in detail.replace('/', ',').split(','):
                    kw = kw.strip()
                    if kw:
                        other_keywords.append(kw)
                # 번호 매핑
                found = ALLERGY_TYPE_TO_NUMBERS.get(detail, [])
                if found:
                    child_allergy_nums.update(found)
                else:
                    for part in re.split(r'[,\s/]+', detail):
                        part = part.strip()
                        if part:
                            nums = ALLERGY_TYPE_TO_NUMBERS.get(part, [])
                            if nums:
                                child_allergy_nums.update(nums)
                            else:
                                ai_nums = _ai_map_other_allergy(part)
                                child_allergy_nums.update(ai_nums)
            else:
                nums = ALLERGY_TYPE_TO_NUMBERS.get(ca.allergy_type, [])
                child_allergy_nums.update(nums)

    if role == 'parent':
        user_id = wiz.session.get("id")
        if user_id:
            try:
                child_ids = [c.id for c in Children.select().where(Children.user_id == int(user_id))]
                if child_ids:
                    _collect_allergy_data(ChildAllergies.select().where(ChildAllergies.child_id.in_(child_ids)))
            except Exception:
                pass
    elif role in ('teacher', 'director'):
        try:
            parent_ids = [sm.user_id for sm in ServerMembers.select(ServerMembers.user_id).where(
                (ServerMembers.server_id == server_id) & (ServerMembers.role == "parent")
            )]
            if parent_ids:
                child_ids = [c.id for c in Children.select().where(Children.user_id.in_(parent_ids))]
                if child_ids:
                    _collect_allergy_data(ChildAllergies.select().where(ChildAllergies.child_id.in_(child_ids)))
        except Exception:
            pass

    if child_allergy_nums or other_keywords:
        for meal_type in meal_allergy:
            meal_nums = set(meal_allergy[meal_type])
            dish_allergy = meal_dish_allergy_map.get(meal_type, {})
            content = meal_content_map.get(meal_type, '')
            matched_names = set()

            # 1. dish_allergies 기반 정밀 매칭 (번호 교차)
            if dish_allergy:
                for dish_name, dish_nums in dish_allergy.items():
                    overlap = child_allergy_nums & set(dish_nums)
                    if overlap:
                        for num in overlap:
                            matched_names.add(ALLERGY_MAP.get(num, str(num)))

            # 2. 전체 번호 교차 매칭 (fallback)
            if not matched_names:
                overlap = child_allergy_nums & meal_nums
                for num in overlap:
                    matched_names.add(ALLERGY_MAP.get(num, str(num)))

            # 3. 기타 알레르기 키워드 텍스트 매칭
            for kw in other_keywords:
                if _keyword_in_content(kw, content):
                    matched_names.add(kw)

            if matched_names:
                allergy_warnings[meal_type] = sorted(matched_names)

    # 학부모: 자녀 연령에 맞게 식단 content 변환 (green 분기 + 연결 메뉴)
    if role == 'parent':
        user_id = wiz.session.get("id")
        age_group = '1~2세'
        if user_id:
            children_info = _get_my_children_info(user_id)
            if children_info:
                child_age = children_info[0]['age']
                age_group = '3~5세' if child_age >= 3 else '1~2세'
        morning_snack = _adapt_content_for_age(morning_snack, age_group)
        lunch = _adapt_content_for_age(lunch, age_group)
        afternoon_snack = _adapt_content_for_age(afternoon_snack, age_group)

    wiz.response.status(200, role=role,
        morning_snack=morning_snack, lunch=lunch, afternoon_snack=afternoon_snack,
        meal_allergy=meal_allergy, allergy_map=ALLERGY_MAP,
        allergy_warnings=allergy_warnings)

def recommend_dinner():
    _recommend_dinner_impl()

def _recommend_dinner_impl():
    role = wiz.session.get("role")
    if not role:
        wiz.response.status(401, message="로그인이 필요합니다.")

    user_id = wiz.session.get("id")
    server_id = _get_server_id()
    meals = _get_today_meals(server_id)
    if not meals:
        wiz.response.status(200, analysis=None, error="오늘 등록된 식단이 없어 추천이 어렵습니다.")

    nutrition_api = wiz.model("nutrition_api")

    # 자녀 정보 조회 (나이에 따라 kcal vs kcal_35 선택에 필요)
    children_info = []
    child_name = ''
    child_age = 0
    if role == "parent" and user_id:
        children_info = _get_my_children_info(user_id)
    if children_info:
        child_name = children_info[0]['name']
        child_age = children_info[0]['age']

    print(f"[recommend_dinner] 자녀: {child_name}, 나이: {child_age}세, 연령그룹: {'3~5세' if child_age >= 3 else '1~2세'}")
    print(f"[recommend_dinner] 오늘 식단 {len(meals)}끼: {[m['meal_type'] for m in meals]}")

    # ── 전처리: content를 그대로 전달 (green 마커는 search_meal에서 처리) ──
    from concurrent.futures import ThreadPoolExecutor

    meal_cleaned = {}
    for m in meals:
        meal_cleaned[m['meal_type']] = m['content'] or ''

    # 3끼 식단을 병렬 조회 (아이 연령 기반 1인분 제공량 적용)
    age_group = '3~5세' if child_age >= 3 else '1~2세'
    meal_results = {}
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(nutrition_api.search_meal, meal_cleaned[m['meal_type']], age_group): m['meal_type'] for m in meals}
        for future in futures:
            meal_type = futures[future]
            try:
                meal_results[meal_type] = future.result()
            except Exception:
                meal_results[meal_type] = {'menus': [], 'total': {}, 'found_count': 0, 'total_count': 0}

    # ── Stage 1: 식약처 API 원본 조회 (green 제외) ──
    stage1_meals = []
    raw_total = {k: 0.0 for k in DAYCARE_TARGET}

    # ── Stage 2: 어린이집 제공 총열량 기준 비율 보정 ──
    stage2_meals = []
    grand_total = {k: 0.0 for k in DAYCARE_TARGET}

    # DB의 kcal은 점심 행에만 저장되어 있지만 실제로는 일일 합계(점심+간식)
    # 아이 나이에 따라 1~2세(kcal) 또는 3~5세(kcal_35) 선택
    daily_total_kcal = None
    daily_total_protein = None
    for m in meals:
        if child_age >= 3:
            if m.get('kcal_35'):
                daily_total_kcal = m['kcal_35']
            if m.get('protein_35'):
                daily_total_protein = m['protein_35']
        else:
            if m.get('kcal'):
                daily_total_kcal = m['kcal']
            if m.get('protein'):
                daily_total_protein = m['protein']

    print(f"[recommend_dinner] DB열량 선택: daily_total_kcal={daily_total_kcal}, daily_total_protein={daily_total_protein} ({'kcal_35/protein_35' if child_age >= 3 else 'kcal/protein'})")

    # 끼니별 에너지 비율 (합이 1.0이 되도록 정규화)
    MEAL_RATIO = {'오전간식': 0.10, '점심': 0.35, '오후간식': 0.10}
    ratio_sum = sum(MEAL_RATIO.get(m['meal_type'], 0.10) for m in meals)
    meal_kcal_map = {}
    meal_protein_map = {}
    if daily_total_kcal and daily_total_kcal > 0:
        for m in meals:
            r = MEAL_RATIO.get(m['meal_type'], 0.10) / ratio_sum
            meal_kcal_map[m['meal_type']] = round(daily_total_kcal * r)
            if daily_total_protein:
                meal_protein_map[m['meal_type']] = round(daily_total_protein * r, 1)

    print(f"[recommend_dinner] 끼니별 DB열량 배분: {meal_kcal_map}")
    print(f"[recommend_dinner] 끼니별 DB단백질 배분: {meal_protein_map}")

    for m in meals:
        db_kcal = meal_kcal_map.get(m['meal_type'])
        db_protein = meal_protein_map.get(m['meal_type'])

        meal_result = meal_results[m['meal_type']]

        # 원본 아이템만의 API 합산 (substitute 제외) — DB kcal은 원본 메뉴 기준이므로
        NUTRIENT_KEYS = ['calories', 'protein', 'fat', 'carbohydrate', 'calcium', 'iron', 'sugar', 'fiber', 'phosphorus', 'potassium', 'sodium', 'vitamin_a', 'vitamin_c']
        original_api_cal = 0.0
        original_api_total = {k: 0.0 for k in NUTRIENT_KEYS}
        for menu in meal_result['menus']:
            if not menu.get('is_substitute', False) and menu['found'] and menu['nutrition']:
                for nk in NUTRIENT_KEYS:
                    v = menu['nutrition'].get(nk)
                    if v is not None:
                        try:
                            original_api_total[nk] += float(v)
                        except (ValueError, TypeError):
                            pass
        original_api_cal = original_api_total.get('calories', 0)

        print(f"[Stage1] {m['meal_type']}: 메뉴 {meal_result['total_count']}개 검색, 성공 {meal_result['found_count']}개, 원본API합산={round(original_api_cal,1)}kcal, DB열량={db_kcal}")

        # DB 열량 기반 스케일링 비율 계산 — 원본 아이템 기준
        if db_kcal and db_kcal > 0 and original_api_cal > 0:
            ratio = db_kcal / original_api_cal
            print(f"[스케일링] {m['meal_type']}: 원본API={round(original_api_cal,1)}kcal → DB={db_kcal}kcal, ratio={ratio:.4f}")

            # protein 별도 ratio (DB protein이 있으면)
            original_api_protein = original_api_total.get('protein', 0)
            if db_protein and db_protein > 0 and original_api_protein > 0:
                protein_ratio = db_protein / original_api_protein
            else:
                protein_ratio = ratio
        else:
            ratio = 1.0
            protein_ratio = 1.0
            print(f"[스케일링] {m['meal_type']} 미적용: 원본API={round(original_api_cal,1)}kcal, DB_kcal={db_kcal}")

        # Stage 1: 원본 아이템만 DB 열량에 맞춰 스케일링, substitute는 참고용
        raw_items = []
        for menu in meal_result['menus']:
            item_data = {
                'name': menu['name'],
                'source': 'api' if menu['found'] else 'unknown',
                'is_substitute': menu.get('is_substitute', False)
            }
            if menu['found'] and menu['nutrition']:
                if menu.get('is_substitute', False):
                    # substitute는 스케일링 없이 원본 API 값 (참고용)
                    item_data.update(_to_display_nutrients(menu['nutrition'], 1.0))
                else:
                    # 원본 아이템: protein은 protein_ratio, 나머지는 kcal ratio
                    scaled_nut = {}
                    for nk in NUTRIENT_KEYS:
                        nv = menu['nutrition'].get(nk)
                        v = float(nv) if nv is not None else 0.0
                        if nk == 'protein':
                            scaled_nut[nk] = round(v * protein_ratio, 2)
                        else:
                            scaled_nut[nk] = round(v * ratio, 2)
                    item_data.update(_to_display_nutrients(scaled_nut, 1.0))
            else:
                item_data.update({k: 0 for k in DAYCARE_TARGET})
            raw_items.append(item_data)

        # subtotal: 원본 아이템만 합산 (= DB kcal/protein과 일치해야 함)
        raw_sub = {k: 0.0 for k in DAYCARE_TARGET}
        for it in raw_items:
            if not it.get('is_substitute', False):
                for k in raw_sub:
                    raw_sub[k] = round(raw_sub[k] + it.get(k, 0), 1)

        stage1_meals.append({
            'meal_type': m['meal_type'],
            'items': raw_items,
            'subtotal': raw_sub
        })
        for k in raw_total:
            raw_total[k] = round(raw_total[k] + raw_sub.get(k, 0), 1)

        # Stage 2: 동일 값 사용
        stage2_meals.append({
            'meal_type': m['meal_type'],
            'items': raw_items,
            'subtotal': dict(raw_sub),
            'target_kcal': db_kcal or None,
            'target_protein': db_protein or None,
            'scale_ratio': round(ratio, 4)
        })

        for k in grand_total:
            grand_total[k] = round(grand_total[k] + raw_sub.get(k, 0), 1)

    stage1 = {'meals': stage1_meals, 'total': raw_total}
    print(f"[Stage1 합계] 스케일링 후 총열량: {raw_total}")
    print(f"[Stage2 합계] 보정 후 총열량: {grand_total}")

    # ── Stage 2: 보정된 수치 + 권장량 대비 부족분 (서버에서 직접) ──

    # 자녀 나이에 따라 DAYCARE_TARGET 동적 선택
    target = _get_daycare_target(child_age)
    print(f"[Stage2] 선택된 목표(child_age={child_age}): {target}")

    consumed = dict(grand_total)
    deficit = {}
    surplus = {}
    status = {}
    for k in target:
        diff = round(consumed.get(k, 0) - target[k], 1)
        if diff < 0:
            deficit[k] = round(abs(diff), 1)
            surplus[k] = 0
            status[k] = '부족'
        elif diff > target[k] * 0.1:
            deficit[k] = 0
            surplus[k] = round(diff, 1)
            status[k] = '초과'
        else:
            deficit[k] = 0
            surplus[k] = 0
            status[k] = '적정'

    print(f"[Stage2] consumed={consumed}")
    print(f"[Stage2] deficit={deficit}")
    print(f"[Stage2] status={status}")

    stage2 = {
        'meals': stage2_meals,
        'child_name': child_name,
        'age': child_age,
        'recommended': dict(target),
        'consumed': consumed,
        'deficit': deficit,
        'surplus': surplus,
        'status': status
    }

    # ── Stage 3: AI에게 저녁 메뉴 추천만 요청 ──
    allergy_text = ""
    if children_info:
        for ci in children_info:
            if ci['allergies']:
                allergy_text = f"알레르기: {', '.join(ci['allergies'])}\n"

    deficit_parts = []
    for k, v in deficit.items():
        if v > 0:
            label, unit = NUTRIENT_LABEL_MAP.get(k, (k, ''))
            deficit_parts.append(f"{label} {v}{unit}")
    deficit_text = ", ".join(deficit_parts) if deficit_parts else "부족 영양소 없음"

    consumed_text = ", ".join([
        f"{NUTRIENT_LABEL_MAP.get(k, (k, ''))[0]} {consumed.get(k, 0)}{NUTRIENT_LABEL_MAP.get(k, (k, ''))[1]}"
        for k in target
    ])

    system_instruction = """당신은 어린이 영양 전문가입니다. 부족 영양소를 채우는 가정식 저녁 메뉴를 추천합니다.
반드시 아래 JSON 형식으로만 응답하세요.
{"menus": [{"name": "메뉴명", "description": "간단 설명", "nutrients": {"calories": 0, "protein": 0, "fat": 0, "carbs": 0, "calcium": 0, "iron": 0}, "reason": "추천 이유"}], "tip": "간단한 조리 팁"}
규칙:
- 알레르기 식품은 절대 포함 금지
- 내가 제공한 칼로리/영양소 수치를 절대 다시 계산하거나 추측하지 마세요
- 영양소 단위: calories=kcal, protein/fat/carbs=g, calcium/iron=mg
- 가정에서 쉽게 만들 수 있는 메뉴 2~3개 추천
- 부족한 영양소를 채우는 메뉴 우선"""

    age_group = '3~5세' if child_age >= 3 else '1~2세'
    prompt = f"""{age_group} 아이의 오늘 어린이집 식사 영양 정보:
실제 섭취량: {consumed_text}
부족 영양소: {deficit_text}

{allergy_text}
부족한 영양소를 보충할 수 있는 저녁 메뉴를 추천해주세요. 저녁 메뉴의 칼로리는 부족분({deficit.get('calories', 0)}kcal)에 맞춰주세요."""

    stage3 = {'menus': [], 'tip': ''}
    try:
        gemini = wiz.model("gemini")
        result = gemini.ask_json(prompt, system_instruction=system_instruction)
        if isinstance(result, dict):
            stage3 = result
    except Exception:
        pass

    analysis = {'stage1': stage1, 'stage2': stage2, 'stage3': stage3}
    wiz.response.status(200, analysis=analysis)

def get_allergy_substitutes():
    role = wiz.session.get("role")
    if role not in ['teacher', 'director']:
        wiz.response.status(403, message="권한이 없습니다.")

    server_id = _get_server_id()
    meals = _get_today_meals(server_id)
    if not meals:
        wiz.response.status(200, substitutes=[])

    all_allergy_numbers = set()
    for m in meals:
        for n in m['allergy_numbers']:
            all_allergy_numbers.add(n)

    if not all_allergy_numbers:
        wiz.response.status(200, substitutes=[])

    menu_text = "\n".join(f"- {m['meal_type']}: {m['content']}" for m in meals)

    child_detail_map = {}
    for c in Children.select().where(Children.user_id.in_([sm.user_id for sm in ServerMembers.select(ServerMembers.user_id).where(
        (ServerMembers.server_id == server_id) & (ServerMembers.role == "parent")
    )])):
        child_detail_map[c.id] = {'name': c.name, 'birthdate': str(c.birthdate) if c.birthdate else ''}

    category_info = ""
    try:
        for cat in AllergyCategories.select():
            category_info += f"- {cat.category_name}: 주의식품=[{cat.caution_foods}], 대체식품=[{cat.substitute_foods}]\n"
    except Exception:
        pass

    allergy_children = []
    try:
        for ar in ChildAllergies.select().where(ChildAllergies.child_id.in_(list(child_detail_map.keys()))):
            child = child_detail_map.get(ar.child_id, {})
            if not child:
                continue
            allergy_children.append({
                'name': child.get('name', ''),
                'birthdate': child.get('birthdate', ''),
                'allergy_type': ar.allergy_type,
                'other_detail': ar.other_detail or ''
            })
    except Exception:
        pass

    if not allergy_children:
        wiz.response.status(200, substitutes=[])

    children_text = ""
    for ac in allergy_children:
        atype = ac['allergy_type']
        if atype == '기타' and ac['other_detail']:
            atype = f"기타({ac['other_detail']})"
        age_info = ""
        if ac['birthdate']:
            try:
                bd = datetime.datetime.strptime(ac['birthdate'], "%Y-%m-%d").date()
                today = datetime.datetime.now(KST).date()
                age_months = (today - bd).days // 30
                age_years = age_months // 12
                kcal = "420kcal" if age_years <= 2 else "640kcal"
                age_info = f", 만{age_years}세, 기준칼로리={kcal}"
            except Exception:
                pass
        children_text += f"- {ac['name']}: 알레르기={atype}{age_info}\n"

    system_instruction = """당신은 어린이 영양사입니다. 알레르기가 있는 아이에게 대체 메뉴를 추천합니다.
반드시 한국어로 답변하세요. 반드시 아래 JSON 배열 형식으로만 답변하세요.
[{"child_name": "이름", "original_menu": "먹을 수 없는 원래 메뉴", "substitute_menu": "대체 추천 메뉴", "reason": "이유 (1줄)"}]"""

    prompt = f"""오늘 어린이집 식단:
{menu_text}

알레르기 아동 정보:
{children_text}

대체식품 참고 정보:
{category_info}

각 아이가 오늘 식단에서 알레르기 때문에 먹을 수 없는 메뉴를 식별하고,
1~2세 칼로리 기준(420kcal)에 맞는 대체 메뉴를 추천해주세요."""

    try:
        gemini = wiz.model("gemini")
        result = gemini.ask_json(prompt, system_instruction=system_instruction)
    except Exception as e:
        wiz.response.status(200, substitutes=[])
    if isinstance(result, list):
        wiz.response.status(200, substitutes=result)
    wiz.response.status(200, substitutes=[])
