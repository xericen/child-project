# pyright: reportUndefinedVariable=false, reportMissingImports=false
import datetime
import json

Meals = wiz.model("db/childcheck/meals")
Children = wiz.model("db/childcheck/children")
ChildAllergies = wiz.model("db/childcheck/child_allergies")
AllergyCategories = wiz.model("db/childcheck/allergy_categories")
ServerMembers = wiz.model("db/login_db/server_members")
Users = wiz.model("db/login_db/users")
MealNutritionCache = wiz.model("db/childcheck/meal_nutrition_cache")
MealSubstituteSelections = wiz.model("db/childcheck/meal_substitute_selections")

KST = datetime.timezone(datetime.timedelta(hours=9))

def _get_gemini():
    """매 호출마다 config에서 최신 API 키를 읽어 fresh Client 생성"""
    from google import genai as _genai
    config = wiz.config("ai")
    api_key = config.gemini.api_key
    model_name = config.gemini.model

    class FreshGemini:
        def __init__(self):
            self._api_key = api_key
            self._model_name = model_name

        def _get_client(self):
            return _genai.Client(api_key=self._api_key)

        def ask(self, prompt, system_instruction=None):
            import time as _time
            cfg = None
            if system_instruction:
                cfg = {"system_instruction": system_instruction}
            for attempt in range(3):
                try:
                    client = self._get_client()
                    response = client.models.generate_content(
                        model=self._model_name,
                        contents=prompt,
                        config=cfg
                    )
                    return response.text
                except Exception as e:
                    if '429' in str(e) and attempt < 2:
                        wait = 10 * (attempt + 1)
                        print(f"[Gemini] 429 rate limit, {wait}s 후 재시도 ({attempt+1}/3)")
                        _time.sleep(wait)
                    else:
                        raise

        def ask_json(self, prompt, system_instruction=None):
            import json as _json
            text = self.ask(prompt, system_instruction=system_instruction)
            if text is None:
                return None
            try:
                cleaned = text.strip()
                if cleaned.startswith("```"):
                    lines = cleaned.split("\n")
                    lines = lines[1:]
                    if lines and lines[-1].strip() == "```":
                        lines = lines[:-1]
                    cleaned = "\n".join(lines)
                return _json.loads(cleaned)
            except Exception:
                return None

    return FreshGemini()

def _parse_menu_names(content, age_group):
    """식단 content에서 음식명 목록 추출 (green 마커, 연령별 분기 처리)"""
    import re
    GREEN_PATTERN = re.compile(r'\{\{green:.*?\}\}')
    AGE_MENU_PAIRS = [('백김치', '배추김치')]

    # 연령별 연결 메뉴 분리
    for young_menu, old_menu in AGE_MENU_PAIRS:
        young_pat = r'\s*'.join(re.escape(ch) for ch in young_menu)
        old_pat = r'\s*'.join(re.escape(ch) for ch in old_menu)
        pattern = young_pat + r'\s*' + old_pat
        replacement = young_menu if age_group == '1~2세' else old_menu
        content = re.sub(pattern, replacement, content)

    CLEAN_PATTERN = re.compile(r'[ⓢⓄ①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳\d.]')
    items = []  # (name, is_substitute)
    prev_idx = None

    for line in content.replace('\r\n', '\n').split('\n'):
        line = line.strip()
        if not line:
            continue
        greens = GREEN_PATTERN.findall(line)
        line_cleaned = GREEN_PATTERN.sub('', line).strip()

        if greens:
            for raw in greens:
                gn = CLEAN_PATTERN.sub('', raw.replace('{{green:', '').replace('}}', '')).strip()
                if gn and gn not in ('/', '-'):
                    if age_group == '1~2세':
                        items.append((gn, False))
                        if prev_idx is not None:
                            items[prev_idx] = (items[prev_idx][0], True)
                    else:
                        items.append((gn, True))
            if line_cleaned:
                cleaned = CLEAN_PATTERN.sub('', line_cleaned).strip()
                if cleaned and cleaned not in ('/', '-'):
                    prev_idx = len(items)
                    items.append((cleaned, False))
                else:
                    prev_idx = None
            else:
                prev_idx = None
        else:
            cleaned = CLEAN_PATTERN.sub('', line).strip()
            if cleaned and cleaned not in ('/', '-'):
                prev_idx = len(items)
                items.append((cleaned, False))

    return items

def _ai_estimate_calcium_iron(food_list, age_group, child_age):
    """AI에게 칼슘/철분만 추정 요청 (칼로리/탄단지는 이미 식약처 DB에서 확보).
    food_list: [{'meal': '점심', 'name': '잡곡밥', 'calories': 100, 'protein': 3.5}, ...]
    Returns: {'잡곡밥': {'calcium': 5.0, 'iron': 0.3}, ...}"""
    if not food_list:
        return {}
    gemini = _get_gemini()
    foods_text = "\n".join([
        f"- [{f['meal']}] {f['name']} ({f['calories']}kcal, 단백질 {f['protein']}g)"
        for f in food_list
    ])
    age_key = '3~5' if child_age >= 3 else '1~2'
    target = DAYCARE_TARGETS.get(age_key, DAYCARE_TARGET)

    prompt = f"""어린이집 {age_group} 아이의 급식 식단입니다. 각 음식의 **칼슘(mg)과 철분(mg)**만 추정해주세요.
칼로리/단백질은 이미 식약처 DB에서 확인된 값입니다.

식단:
{foods_text}

어린이집 {age_group} 급식 일일 목표: 칼슘 {target.get('calcium', 250)}mg, 철분 {target.get('iron', 3.3)}mg

참고사항:
- 쌀밥/잡곡밥: 칼슘 낮음(2~5mg), 철분 낮음(0.1~0.3mg)
- 국/탕류: 칼슘 보통(10~30mg), 철분 보통(0.3~0.8mg)
- 육류(닭/소/돼지): 칼슘 낮음(5~15mg), 철분 높음(0.5~1.5mg)
- 유제품(우유/요거트/치즈): 칼슘 높음(100~200mg), 철분 매우 낮음(0~0.1mg)
- 김치류: 칼슘 보통(15~30mg), 철분 보통(0.3~0.5mg)
- 두유: 칼슘 높음(30~50mg), 철분 보통(0.3~0.5mg)
- 고구마: 칼슘 낮음(10~20mg), 철분 보통(0.3~0.5mg)
- 과일류: 칼슘 낮음(3~10mg), 철분 낮음(0.1~0.3mg)

모든 수치는 {age_group} 아이 1인분 기준입니다.
전체 합산이 일일 목표에 근접하도록 배분해주세요.

반드시 아래 JSON 형식으로만 응답하세요:
{{"음식이름": {{"calcium": 0, "iron": 0}}, ...}}"""

    system = "어린이집 급식 영양 분석 전문가입니다. 칼슘과 철분 수치만 정확히 추정합니다. JSON만 응답하세요."
    try:
        result = gemini.ask_json(prompt, system_instruction=system)
        if isinstance(result, dict):
            print(f"[AI추정] 칼슘/철분 {len(result)}개 음식 추정 완료")
            return result
    except Exception as e:
        print(f"[AI추정] 칼슘/철분 추정 실패: {e}")
    return {}


def _ai_analyze_all_meals(meal_foods, age_group, db_kcal, db_protein, child_age):
    """2단계 영양분석 파이프라인:
    [Phase 1] 식약처 DB → 칼로리/탄단지/칼슘/철분 (per 100g → 1인분 환산)
    [Phase 2] 식단표 열량 기준 비율 보정 + total 열량/단백질은 DB값 직접 사용"""

    print(f"[영양분석] ===== 2단계 파이프라인 시작 =====")
    print(f"[영양분석] 연령그룹: {age_group}, 나이: {child_age}세")
    print(f"[영양분석] 식단표 등록값 → 열량: {db_kcal}kcal, 단백질: {db_protein}g")

    age_key = '3~5' if child_age >= 3 else '1~2'
    target = DAYCARE_TARGETS.get(age_key, DAYCARE_TARGET)

    # ── Phase 1: 식약처 DB에서 칼로리/탄단지 조회 ──
    print(f"[Phase1] 식약처 DB 검색 시작...")
    nutrition_api = wiz.model("nutrition_api")

    all_items_by_meal = {}  # {meal_type: [item_dict, ...]}

    for mt in ['오전간식', '점심', '오후간식']:
        content = meal_foods.get(mt, '')
        if not content:
            continue

        pipeline_result = nutrition_api.analyze_meal_pipeline(content, age_group)

        items = []
        api_count = 0
        ai_count = 0

        for menu in pipeline_result.get('menus', []):
            nutrition = menu.get('nutrition') or {}
            is_sub = menu.get('is_substitute', False)
            is_estimated = menu.get('is_estimated', False)
            found = menu.get('found', False)

            if not found:
                source = 'error'
            elif is_estimated:
                source = 'ai_estimate'
                ai_count += 1
            else:
                source = 'api'
                api_count += 1

            # Phase 1: 식약처 DB에서 칼로리/탄단지/칼슘/철분 모두 가져옴
            item = {
                'name': menu['name'],
                'source': source,
                'is_substitute': is_sub,
                'is_estimated': is_estimated,
                'matched_name': nutrition.get('name', menu['name']),
                'serving_size': nutrition.get('serving_size', '1인분'),
                'serving_ratio': nutrition.get('serving_ratio', 1.0),
                'category': nutrition.get('category', ''),
                'calories': round(float(nutrition.get('calories', 0)), 1),
                'protein': round(float(nutrition.get('protein', 0)), 1),
                'fat': round(float(nutrition.get('fat', 0)), 1),
                'carbs': round(float(nutrition.get('carbohydrate', nutrition.get('carbs', 0))), 1),
                'calcium': round(float(nutrition.get('calcium', 0)), 1),
                'iron': round(float(nutrition.get('iron', 0)), 1),
            }
            items.append(item)

        print(f"[Phase1] {mt}: 식약처DB {api_count}건, AI보완 {ai_count}건")
        for item in items:
            if not item['is_substitute']:
                print(f"[Phase1]   {item['name']} → {item['matched_name']} ({item['source']}) cal={item['calories']} p={item['protein']} f={item['fat']} c={item['carbs']}")

        all_items_by_meal[mt] = items

    # ── Phase 2: 식단표 등록 열량/단백질에 맞춰 비례 스케일링 ──
    # 대체식 제외한 합계 계산
    raw_total_cal = 0.0
    raw_total_prot = 0.0
    raw_total_fat = 0.0
    raw_total_carbs = 0.0
    raw_total_calcium = 0.0
    raw_total_iron = 0.0
    for mt_items in all_items_by_meal.values():
        for item in mt_items:
            if not item['is_substitute']:
                raw_total_cal += item['calories']
                raw_total_prot += item['protein']
                raw_total_fat += item['fat']
                raw_total_carbs += item['carbs']
                raw_total_calcium += item['calcium']
                raw_total_iron += item['iron']

    print(f"[Phase2] API RAW 합계: cal={round(raw_total_cal, 1)} prot={round(raw_total_prot, 1)} fat={round(raw_total_fat, 1)} carbs={round(raw_total_carbs, 1)} ca={round(raw_total_calcium, 1)} fe={round(raw_total_iron, 1)}")

    # 스케일링 비율 계산
    cal_ratio = 1.0
    prot_ratio = 1.0
    if db_kcal and db_kcal > 0 and raw_total_cal > 0:
        cal_ratio = db_kcal / raw_total_cal
        print(f"[Phase2] 열량 스케일: {round(raw_total_cal, 1)}kcal → {db_kcal}kcal (×{cal_ratio:.3f})")
    if db_protein and db_protein > 0 and raw_total_prot > 0:
        prot_ratio = db_protein / raw_total_prot
        print(f"[Phase2] 단백질 스케일: {round(raw_total_prot, 1)}g → {db_protein}g (×{prot_ratio:.3f})")

    # 스케일링 적용: 모든 영양소를 열량비율로, 단백질만 단백질비율로
    for mt_items in all_items_by_meal.values():
        for item in mt_items:
            if item['is_substitute']:
                continue
            item['calories'] = round(item['calories'] * cal_ratio, 1)
            item['protein'] = round(item['protein'] * prot_ratio, 1)
            item['fat'] = round(item['fat'] * cal_ratio, 1)
            item['carbs'] = round(item['carbs'] * cal_ratio, 1)
            item['calcium'] = round(item['calcium'] * cal_ratio, 1)
            item['iron'] = round(item['iron'] * cal_ratio, 1)

    # 스케일링 후 합계 확인
    scaled_cal = sum(item['calories'] for mt_items in all_items_by_meal.values() for item in mt_items if not item['is_substitute'])
    scaled_prot = sum(item['protein'] for mt_items in all_items_by_meal.values() for item in mt_items if not item['is_substitute'])
    scaled_fat = sum(item['fat'] for mt_items in all_items_by_meal.values() for item in mt_items if not item['is_substitute'])
    scaled_carbs = sum(item['carbs'] for mt_items in all_items_by_meal.values() for item in mt_items if not item['is_substitute'])
    scaled_calcium = sum(item['calcium'] for mt_items in all_items_by_meal.values() for item in mt_items if not item['is_substitute'])
    scaled_iron = sum(item['iron'] for mt_items in all_items_by_meal.values() for item in mt_items if not item['is_substitute'])
    print(f"[Phase2] 스케일링 후: cal={round(scaled_cal, 1)} prot={round(scaled_prot, 1)} fat={round(scaled_fat, 1)} carbs={round(scaled_carbs, 1)} ca={round(scaled_calcium, 1)} fe={round(scaled_iron, 1)}")

    # ── 결과 조립 ──
    stage1_meals = []
    total = {k: 0.0 for k in DAYCARE_TARGET}

    for mt in ['오전간식', '점심', '오후간식']:
        items = all_items_by_meal.get(mt, [])
        if not items:
            continue

        sub_total = {k: 0.0 for k in DAYCARE_TARGET}
        for item in items:
            if not item['is_substitute']:
                for k in DAYCARE_TARGET:
                    sub_total[k] = round(sub_total[k] + item.get(k, 0), 1)

        stage1_meals.append({
            'meal_type': mt,
            'items': items,
            'subtotal': sub_total
        })
        for k in total:
            total[k] = round(total[k] + sub_total.get(k, 0), 1)

    # DB 값으로 total 열량/단백질 강제 고정 (개별 스케일링 합산의 반올림 오차 제거)
    if db_kcal and db_kcal > 0:
        total['calories'] = float(db_kcal)
    if db_protein and db_protein > 0:
        total['protein'] = float(db_protein)

    print(f"[영양분석] ===== 최종 결과 =====")
    print(f"[영양분석] cal={total['calories']}kcal prot={total['protein']}g fat={total['fat']}g carbs={total['carbs']}g ca={total['calcium']}mg fe={total['iron']}mg")
    api_total = sum(1 for mt_items in all_items_by_meal.values() for item in mt_items if item['source'] == 'api' and not item['is_substitute'])
    ai_total = sum(1 for mt_items in all_items_by_meal.values() for item in mt_items if item['source'] != 'api' and not item['is_substitute'])
    print(f"[영양분석] 식약처DB: {api_total}건, AI보완: {ai_total}건")

    return {'meals': stage1_meals, 'total': total}

def _ai_verify_nutrition(items, age_group, total):
    """AI 최종 검증: 각 음식의 칼로리가 어린이 1인분 기준으로 합리적인지 확인.
    이상한 항목이 있으면 보정된 영양소 dict를 반환.
    Returns: {food_name: {calories: ..., protein: ..., ...}} or None"""
    if not items:
        return None
    try:
        gemini = _get_gemini()
        items_str = json.dumps(items, ensure_ascii=False)
        total_str = json.dumps(total, ensure_ascii=False)
        prompt = f"""어린이집 급식표의 각 음식별 영양 분석 결과를 검증해주세요.
대상 연령: {age_group} 어린이

각 음식 분석 결과:
{items_str}

전체 합계: {total_str}

검증 기준:
1. 각 음식의 칼로리가 {age_group} 아이의 1인분 기준으로 합리적인가?
2. 원래 음식(name)과 매칭된 식품(matched_name)이 같은 음식인가? (조리법이 다르면 불일치)
3. 카테고리가 원래 음식의 실제 조리법과 맞는가?
4. 전체 합계가 {age_group} 어린이집 1일 급식(간식+점심) 기준으로 합리적인가?

예시: "찐고구마"가 "고구마전"(전·부침류)으로 매칭됐으면 → 조리법 불일치, 찐고구마로 보정 필요

보정이 필요한 음식만 아래 JSON으로 반환하세요.
모두 합리적이면 빈 객체 {{}} 를 반환하세요.

형식:
{{
  "음식이름": {{
    "reason": "보정 이유",
    "calories": 보정된칼로리, "protein": 보정된단백질g, "fat": 보정된지방g,
    "carbs": 보정된탄수화물g, "calcium": 보정된칼슘mg, "iron": 보정된철분mg
  }}
}}

중요: 보정 수치는 {age_group} 아이의 실제 1인분 기준이어야 합니다."""
        result = gemini.ask_json(prompt)
        if isinstance(result, dict) and len(result) > 0:
            # reason 키 제외하고 반환
            corrections = {}
            for name, fix in result.items():
                if isinstance(fix, dict) and fix.get('calories', 0) > 0:
                    corrections[name] = {k: v for k, v in fix.items() if k != 'reason'}
                    print(f"[AI검증] {name}: {fix.get('reason', '이유 없음')}")
            return corrections if corrections else None
    except Exception as e:
        print(f"[AI검증] 실패: {e}")
    return None

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
DAYCARE_TARGETS = {
    '1~2': {'calories': 420, 'protein': 20, 'fat': 17, 'carbs': 73, 'calcium': 250, 'iron': 3.3},
    '3~5': {'calories': 640, 'protein': 12.5, 'fat': 23, 'carbs': 102, 'calcium': 275, 'iron': 4.5},
}
DAYCARE_TARGET = DAYCARE_TARGETS['1~2']

# 연령별 하루 전체 권장 섭취량 (급식표 기준)
DAILY_TARGETS = {
    '1~2': {'calories': 900, 'protein': 20, 'fat': 30, 'carbs': 130, 'calcium': 450, 'iron': 6},
    '3~5': {'calories': 1400, 'protein': 25, 'fat': 45, 'carbs': 200, 'calcium': 550, 'iron': 7},
}

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
    """키워드가 식단 content에 매칭되는지 확인.
    1. 직접 문자열 포함 → 'direct'
    2. KEYWORD_ALIASES 별칭 매칭 → 'alias'
    3. AI 재료 캐시 매칭 → 'ingredient'
    4. 미매칭 → 'unknown'
    Returns: (matched: bool, confidence: str)
    """
    if keyword in content:
        return True, 'direct'
    for alias in KEYWORD_ALIASES.get(keyword, []):
        if alias in content:
            return True, 'alias'
    # AI 재료 캐시 확인
    matched_dishes = _get_ingredient_cache(keyword)
    if matched_dishes:
        for dish in matched_dishes:
            if dish in content:
                return True, 'ingredient'
    return False, 'unknown'

_ingredient_cache_store = {}

def _extract_all_food_names(content):
    """식단 content에서 모든 음식명 추출 (마커 제거, 번호 제거)"""
    CLEAN_PATTERN = re.compile(r'[ⓢⓄ①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳\d.]')
    GREEN_PATTERN = re.compile(r'\{\{green:(.*?)\}\}')
    names = set()
    for line in content.replace('\r\n', '\n').split('\n'):
        line = line.strip()
        if not line:
            continue
        for m in GREEN_PATTERN.finditer(line):
            gn = CLEAN_PATTERN.sub('', m.group(1)).strip()
            if gn and gn not in ('/', '-'):
                names.add(gn)
        cleaned = GREEN_PATTERN.sub('', line).strip()
        cleaned = CLEAN_PATTERN.sub('', cleaned).strip()
        if cleaned and cleaned not in ('/', '-'):
            names.add(cleaned)
    return names

def _build_monthly_allergy_cache(server_id, keywords):
    """월간 전체 식단에서 기타 알레르기 키워드가 포함될 수 있는 음식을 Gemini로 일괄 분석하고 캐시.
    keywords: 표준 19종에 해당하지 않는 기타 알레르기 키워드 리스트
    Returns: {keyword: [matched_dish1, ...], ...}
    """
    if not keywords:
        return {}

    today = datetime.datetime.now(KST).date()
    month_str = today.strftime("%Y-%m")
    cache_fs = wiz.project.fs("data", "allergy_ingredient_cache", str(server_id), month_str)
    cache_file = "batch.json"

    # 기존 캐시 로드
    cached = {}
    try:
        if cache_fs.exists(cache_file):
            cached = cache_fs.read.json(cache_file, default={})
    except Exception:
        pass

    # 누락된 키워드만 분석
    missing_keywords = [kw for kw in keywords if kw not in cached]
    if not missing_keywords:
        # 인메모리 캐시 갱신
        for kw in keywords:
            _ingredient_cache_store[kw] = cached.get(kw, [])
        return cached

    # 이번 달 전체 식단 음식명 수집
    first_of_month = today.replace(day=1)
    if today.month == 12:
        next_month_first = today.replace(year=today.year + 1, month=1, day=1)
    else:
        next_month_first = today.replace(month=today.month + 1, day=1)
    last_of_month = next_month_first - datetime.timedelta(days=1)

    all_foods = set()
    try:
        meals = Meals.select().where(
            (Meals.server_id == server_id) &
            (Meals.meal_date >= first_of_month) &
            (Meals.meal_date <= last_of_month)
        )
        for meal in meals:
            if meal.content:
                all_foods.update(_extract_all_food_names(meal.content))
    except Exception as e:
        print(f"[알레르기캐시] 식단 조회 실패: {e}")

    if not all_foods:
        for kw in missing_keywords:
            cached[kw] = []
        return cached

    # Gemini에 한 번에 질문
    foods_list = sorted(all_foods)
    keywords_str = ", ".join(missing_keywords)
    foods_str = ", ".join(foods_list)

    prompt = f"""다음은 어린이집 한 달 식단의 음식 목록입니다:
{foods_str}

아이가 다음 식재료에 알레르기가 있습니다: {keywords_str}

각 알레르기 키워드에 대해, 위 음식 목록 중 해당 식재료가 **재료로 포함될 가능성이 높은** 음식을 모두 찾아주세요.
음식 이름에 직접적으로 포함된 경우뿐만 아니라, 일반적으로 해당 재료가 들어가는 음식도 포함해주세요.
예) "땅콩" → ["카레라이스", "쿠키"] (카레에 땅콩버터가 들어갈 수 있고, 쿠키에 견과류가 포함될 수 있음)

반드시 아래 JSON 형식으로만 응답하세요:
{{"{missing_keywords[0]}": ["해당 음식1", "해당 음식2"], ...}}
해당 음식이 없으면 빈 배열을 반환하세요."""

    try:
        gemini = _get_gemini()
        result = gemini.ask_json(prompt, system_instruction="식품 알레르기 전문가입니다. JSON만 응답하세요.")
        if isinstance(result, dict):
            for kw in missing_keywords:
                matched = result.get(kw, [])
                if isinstance(matched, list):
                    cached[kw] = [str(d) for d in matched]
                else:
                    cached[kw] = []
            print(f"[알레르기캐시] Gemini 일괄 분석 완료: {len(missing_keywords)}개 키워드, {len(foods_list)}개 음식")
        else:
            for kw in missing_keywords:
                cached[kw] = []
    except Exception as e:
        print(f"[알레르기캐시] Gemini 분석 실패: {e}")
        for kw in missing_keywords:
            cached[kw] = []

    # 파일 캐시 저장
    try:
        cache_fs.write.json(cache_file, cached)
    except Exception as e:
        print(f"[알레르기캐시] 캐시 저장 실패: {e}")

    # 인메모리 캐시 갱신
    for kw in keywords:
        _ingredient_cache_store[kw] = cached.get(kw, [])

    return cached

def _get_ingredient_cache(keyword):
    """월간 일괄 캐시에서 키워드의 매칭 음식 목록을 로드"""
    if keyword in _ingredient_cache_store:
        return _ingredient_cache_store[keyword]
    try:
        server_id = wiz.session.get("server_id") or wiz.session.get("join_server_id")
        if not server_id:
            return []
        month_str = datetime.date.today().strftime("%Y-%m")
        cache_fs = wiz.project.fs("data", "allergy_ingredient_cache", str(server_id), month_str)
        cache_file = "batch.json"
        if cache_fs.exists(cache_file):
            data = cache_fs.read.json(cache_file, default={})
            matched = data.get(keyword, [])
            _ingredient_cache_store[keyword] = matched
            return matched
    except Exception:
        pass
    _ingredient_cache_store[keyword] = []
    return []

_ai_allergy_cache = {}

def _ai_map_other_allergy(other_detail):
    """기타 알레르기 키워드가 표준 19종 중 어디에 해당하는지 AI로 분석 (파일 캐시 적용)."""
    if not other_detail or not other_detail.strip():
        return []
    key = other_detail.strip()
    if key in _ai_allergy_cache:
        return _ai_allergy_cache[key]
    # 파일 캐시 확인 (자체 캐시 + meal 페이지 캐시)
    cache_fs = wiz.project.fs("data", "allergy_ai_cache")
    meal_cache_fs = wiz.project.fs("data", "cache", "allergy_map")
    import hashlib
    cache_file = hashlib.md5(key.encode()).hexdigest() + ".json"
    try:
        if cache_fs.exists(cache_file):
            cached = cache_fs.read.json(cache_file, default=None)
            if cached is not None:
                _ai_allergy_cache[key] = cached
                return cached
    except Exception:
        pass
    try:
        if meal_cache_fs.exists(cache_file):
            cached = meal_cache_fs.read.json(cache_file, default=None)
            if cached is not None and isinstance(cached, list):
                _ai_allergy_cache[key] = cached
                return cached
    except Exception:
        pass
    allergy_list = ", ".join([f"{v}({k}번)" for k, v in ALLERGY_MAP.items()])
    try:
        gemini = _get_gemini()
        prompt = f"""아이의 알레르기가 "{key}"입니다.
표준 19종 알레르기: {allergy_list}
이 알레르기가 표준 19종 중 어떤 항목에 해당하는지 번호만 반환해주세요.
해당하는 게 없으면 빈 배열을 반환하세요.
JSON 형식: {{"numbers": [10]}}"""
        result = gemini.ask_json(prompt, system_instruction="알레르기 전문가입니다. JSON만 응답하세요.")
        if isinstance(result, dict) and 'numbers' in result:
            nums = [int(n) for n in result['numbers'] if isinstance(n, (int, float)) and 1 <= int(n) <= 19]
            _ai_allergy_cache[key] = nums
            try:
                cache_fs.write.json(cache_file, nums)
            except Exception:
                pass
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

def _get_daily_target(age):
    """자녀 나이 기반 하루 전체 권장 섭취량 반환"""
    if age >= 3:
        return DAILY_TARGETS['3~5']
    return DAILY_TARGETS['1~2']

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

def _apply_parent_content(content, meal_id, age_group):
    """학부모용 content 변환: 교사 대체식 선택 반영 + 연령별 분기.
    - 교사가 대체식을 선택(☑)했으면 원본 제거, 대체식만 표시
    - 교사가 선택 안 했으면(☐ 또는 미설정) 원본 유지, 대체식 제거
    - 백김치/배추김치 등 연결 메뉴는 연령에 맞는 것만 표시
    """
    if not content:
        return content

    # 1) 교사 대체식 선택 상태 조회
    sub_map = {}
    try:
        for sel in MealSubstituteSelections.select().where(
            MealSubstituteSelections.meal_id == meal_id
        ):
            sub_map[sel.original_item.strip()] = bool(sel.is_selected)
    except Exception:
        pass

    # 2) green 마커 처리: 교사 선택 기반
    lines = content.split('\n')
    result = []
    prev_line = None
    for line in lines:
        m = _GREEN_RE.search(line)
        if m:
            green_text = re.search(r'\{\{green:(.*?)\}\}', line).group(1).strip()
            remainder = _GREEN_RE.sub('', line).strip()
            is_selected = sub_map.get(prev_line.strip() if prev_line else '', False)
            if is_selected:
                # 대체식 선택됨 → 원본 제거, 대체식 사용
                if result and prev_line is not None:
                    result.pop()
                result.append(green_text)
            else:
                # 대체식 미선택 → 원본 유지, green 제거
                pass
            if remainder:
                result.append(remainder)
            prev_line = remainder if remainder else prev_line
        else:
            result.append(line)
            prev_line = line
    content = '\n'.join(result)

    # 3) 연결 메뉴 분리 (백김치배추김치 → 연령별)
    for young, old in _AGE_MENU_PAIRS:
        young_pat = r'\s*'.join(re.escape(ch) for ch in young)
        old_pat = r'\s*'.join(re.escape(ch) for ch in old)
        pattern = young_pat + r'\s*' + old_pat
        content = re.sub(pattern, young if age_group == '1~2세' else old, content)

    return content

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
                'id': row.id,
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
            age_months = 0
            if child.birthdate:
                age = today.year - child.birthdate.year
                if (today.month, today.day) < (child.birthdate.month, child.birthdate.day):
                    age -= 1
                # 개월 수 계산
                age_months = (today.year - child.birthdate.year) * 12 + (today.month - child.birthdate.month)
                if today.day < child.birthdate.day:
                    age_months -= 1

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
                'age_months': age_months,
                'birthdate': str(child.birthdate) if child.birthdate else '',
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

    # 19종 미해당 기타 키워드 → 월간 AI 일괄 캐시 빌드
    if other_keywords:
        custom_kw = set()
        for kw in set(other_keywords):
            if ALLERGY_TYPE_TO_NUMBERS.get(kw):
                continue
            if kw in KEYWORD_ALIASES:
                continue
            ai_nums = _ai_allergy_cache.get(kw, [])
            if not ai_nums:
                custom_kw.add(kw)
        if custom_kw:
            _build_monthly_allergy_cache(server_id, list(custom_kw))

    allergy_dishes = {}
    if child_allergy_nums or other_keywords:
        for meal_type in meal_allergy:
            meal_nums = set(meal_allergy[meal_type])
            dish_allergy = meal_dish_allergy_map.get(meal_type, {})
            content = meal_content_map.get(meal_type, '')
            matched_names = set()
            matched_dishes = []

            # 1. dish_allergies 기반 정밀 매칭 (번호 교차)
            if dish_allergy:
                for dish_name, dish_nums in dish_allergy.items():
                    overlap = child_allergy_nums & set(dish_nums)
                    if overlap:
                        anames = [ALLERGY_MAP.get(n, str(n)) for n in sorted(overlap)]
                        matched_names.update(anames)
                        # green 마커 제거 후 음식명 정리
                        clean_name = re.sub(r'\{\{green:.*?\}\}', '', dish_name).strip()
                        if not clean_name:
                            clean_name = dish_name
                        matched_dishes.append({'dish': clean_name, 'allergens': anames})

            # 2. 전체 번호 교차 매칭 (fallback)
            if not matched_names:
                overlap = child_allergy_nums & meal_nums
                for num in overlap:
                    matched_names.add(ALLERGY_MAP.get(num, str(num)))

            # 3. 기타 알레르기 키워드 텍스트 매칭 (식단명 → 별칭 → 재료캐시)
            for kw in other_keywords:
                matched, confidence = _keyword_in_content(kw, content)
                if matched:
                    matched_names.add(kw)

            if matched_names:
                allergy_warnings[meal_type] = sorted(matched_names)
            if matched_dishes:
                allergy_dishes[meal_type] = matched_dishes

    # 학부모: 교사 대체식 선택 반영 + 연령별 분기 (백김치/배추김치)
    if role == 'parent':
        user_id = wiz.session.get("id")
        child_age = 3  # 기본값
        if user_id:
            try:
                children_info = _get_my_children_info(user_id)
                if children_info:
                    child_age = children_info[0].get('age', 3)
            except Exception:
                pass
        age_group = '1~2세' if child_age < 3 else '3~5세'
        # meal_id 맵 구성
        meal_id_map = {}
        for m in meals:
            meal_id_map[m['meal_type']] = m.get('id')
        for mt, var_name in [('오전간식', 'morning_snack'), ('점심', 'lunch'), ('오후간식', 'afternoon_snack')]:
            mid = meal_id_map.get(mt)
            if mid:
                if var_name == 'morning_snack':
                    morning_snack = _apply_parent_content(morning_snack, mid, age_group)
                elif var_name == 'lunch':
                    lunch = _apply_parent_content(lunch, mid, age_group)
                elif var_name == 'afternoon_snack':
                    afternoon_snack = _apply_parent_content(afternoon_snack, mid, age_group)

    # 끼니별 칼로리 계산 (연령에 따라 kcal vs kcal_35 선택)
    child_age_for_kcal = 3
    if role == 'parent':
        child_age_for_kcal = child_age
    meal_kcal = {}
    daily_total = None
    for m in meals:
        if child_age_for_kcal >= 3:
            if m.get('kcal_35'):
                daily_total = m['kcal_35']
        else:
            if m.get('kcal'):
                daily_total = m['kcal']
    if daily_total and daily_total > 0:
        # 끼니별 배분 비율 (어린이집 급식 기준: 오전간식 10%, 점심 35%, 오후간식 10%)
        ratios = {'오전간식': 0.10, '점심': 0.35, '오후간식': 0.10}
        total_ratio = sum(ratios.values())
        for mt, ratio in ratios.items():
            meal_kcal[mt] = round(daily_total * ratio / total_ratio)

    wiz.response.status(200, role=role,
        morning_snack=morning_snack, lunch=lunch, afternoon_snack=afternoon_snack,
        meal_allergy=meal_allergy, allergy_map=ALLERGY_MAP,
        allergy_warnings=allergy_warnings, allergy_dishes=allergy_dishes,
        meal_kcal=meal_kcal)

def recommend_dinner():
    try:
        _recommend_dinner_impl()
    except Exception as e:
        # ResponseException은 wiz.response 정상 종료이므로 re-raise
        if type(e).__name__ == 'ResponseException':
            raise
        print(f"[recommend_dinner] ERROR: {e}")
        import traceback
        traceback.print_exc()
        wiz.response.status(500, message=f"저녁 추천 분석 중 오류: {str(e)}")

def _recommend_dinner_impl():
    role = wiz.session.get("role")
    if not role:
        wiz.response.status(401, message="로그인이 필요합니다.")

    user_id = wiz.session.get("id")
    server_id = _get_server_id()
    meals = _get_today_meals(server_id)
    if not meals:
        wiz.response.status(200, analysis=None, error="오늘 등록된 식단이 없어 추천이 어렵습니다.")

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
    if children_info:
        ci = children_info[0]
        print(f"[recommend_dinner] 생년월일: {ci.get('birthdate', '없음')}, 개월수: {ci.get('age_months', 0)}개월")
        print(f"[recommend_dinner] 알레르기: {ci.get('allergies', [])}")
    print(f"[recommend_dinner] 오늘 식단 {len(meals)}끼: {[m['meal_type'] for m in meals]}")

    # ── 전처리: 교사 대체식 선택 반영 + 연령별 분기 ──
    age_group = '3~5세' if child_age >= 3 else '1~2세'
    meal_cleaned = {}
    for m in meals:
        raw = m['content'] or ''
        meal_id = m.get('id')
        adapted = _apply_parent_content(raw, meal_id, age_group) if meal_id else _adapt_content_for_age(raw, age_group)
        meal_cleaned[m['meal_type']] = adapted
        print(f"[recommend_dinner] {m['meal_type']} 전처리({age_group}): {repr(raw[:80])} → {repr(adapted[:80])}")

    # 3끼 식단을 AI 기반으로 영양 분석 (DB 칼로리/단백질을 앵커로 사용)
    # DB에서 일일 합계 칼로리/단백질 가져오기
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

    print(f"[recommend_dinner] DB 기준: kcal={daily_total_kcal}, protein={daily_total_protein}")

    # 끼니별 음식 목록 구성
    meal_foods = {}
    for m in meals:
        mt = m['meal_type']
        meal_foods[mt] = meal_cleaned.get(mt, '')

    # ── 캐시 확인 → 분석 → 캐시 저장 ──
    today = datetime.datetime.now(KST).date()
    cached_stage1 = None
    try:
        cache_row = MealNutritionCache.get_or_none(
            (MealNutritionCache.server_id == server_id) &
            (MealNutritionCache.meal_date == today) &
            (MealNutritionCache.age_group == age_group)
        )
        if cache_row and cache_row.stage1_json:
            cached_stage1 = json.loads(cache_row.stage1_json)
            print(f"[recommend_dinner] 캐시 히트! analyzed_at={cache_row.analyzed_at}")
    except Exception as e:
        print(f"[recommend_dinner] 캐시 조회 실패: {e}")

    if cached_stage1:
        stage1_result = cached_stage1
        print(f"[Stage1] 캐시에서 로드 (DB 분석 스킵)")
    else:
        # 식약처 API + AI 분석 (최초 1회만)
        stage1_result = _ai_analyze_all_meals(
            meal_foods, age_group, daily_total_kcal, daily_total_protein, child_age
        )
        # 캐시에 저장
        try:
            total = stage1_result.get('total', {})
            existing = MealNutritionCache.get_or_none(
                (MealNutritionCache.server_id == server_id) &
                (MealNutritionCache.meal_date == today) &
                (MealNutritionCache.age_group == age_group)
            )
            cache_data = {
                'server_id': server_id,
                'meal_date': today,
                'age_group': age_group,
                'total_calories': total.get('calories', 0),
                'total_protein': total.get('protein', 0),
                'total_fat': total.get('fat', 0),
                'total_carbs': total.get('carbs', 0),
                'total_calcium': total.get('calcium', 0),
                'total_iron': total.get('iron', 0),
                'stage1_json': json.dumps(stage1_result, ensure_ascii=False),
            }
            if existing:
                MealNutritionCache.update(**cache_data).where(
                    MealNutritionCache.id == existing.id
                ).execute()
            else:
                MealNutritionCache.create(**cache_data)
            print(f"[recommend_dinner] 캐시 저장 완료")
        except Exception as e:
            print(f"[recommend_dinner] 캐시 저장 실패: {e}")

    stage1_meals = stage1_result['meals']
    raw_total = stage1_result['total']
    grand_total = dict(raw_total)

    stage1 = {'meals': stage1_meals, 'total': raw_total}
    print(f"[Stage1 합계] AI 분석: {raw_total}")

    # stage2_meals 구성
    stage2_meals = []
    for meal_data in stage1_meals:
        stage2_meals.append({
            'meal_type': meal_data['meal_type'],
            'items': meal_data['items'],
            'subtotal': dict(meal_data['subtotal']),
            'target_kcal': daily_total_kcal,
            'target_protein': daily_total_protein,
        })

    # ── Stage 2: 보정된 수치 + 권장량 대비 부족분 (서버에서 직접) ──

    # 자녀 나이에 따라 DAYCARE_TARGET 동적 선택
    target = _get_daycare_target(child_age)
    print(f"[Stage2] 선택된 목표(child_age={child_age}): {target}")

    consumed = dict(grand_total)

    # 하루 전체 권장 섭취량 (저녁 추천용)
    daily_target = _get_daily_target(child_age)
    dinner_deficit = {}
    for k in daily_target:
        diff = round(daily_target[k] - consumed.get(k, 0), 1)
        dinner_deficit[k] = max(diff, 0)

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
        'status': status,
        'daily_target': dict(daily_target),
        'dinner_deficit': dinner_deficit,
    }

    # ── Stage 3: AI에게 저녁 메뉴 추천만 요청 ──
    print(f"[Stage3] 하루 전체 목표: {daily_target}")
    print(f"[Stage3] 저녁 부족분: {dinner_deficit}")

    allergy_text = ""
    if children_info:
        for ci in children_info:
            if ci['allergies']:
                allergy_text = f"알레르기: {', '.join(ci['allergies'])}\n"

    deficit_parts = []
    for k, v in dinner_deficit.items():
        if v > 0:
            label, unit = NUTRIENT_LABEL_MAP.get(k, (k, ''))
            deficit_parts.append(f"{label} {v}{unit}")
    deficit_text = ", ".join(deficit_parts) if deficit_parts else "부족 영양소 없음"

    consumed_text = ", ".join([
        f"{NUTRIENT_LABEL_MAP.get(k, (k, ''))[0]} {consumed.get(k, 0)}{NUTRIENT_LABEL_MAP.get(k, (k, ''))[1]}"
        for k in daily_target
    ])

    # 아이 나이에 따른 음식 가이드 생성
    child_age_months = 0
    if children_info:
        child_age_months = children_info[0].get('age_months', child_age * 12)
    age_years = child_age_months // 12
    age_remain_months = child_age_months % 12
    age_detail_text = f"만 {age_years}세 {age_remain_months}개월" if age_remain_months > 0 else f"만 {age_years}세"

    if child_age_months <= 18:
        food_guide = """이 아이는 이유식 완료기~유아식 초기 단계입니다.
- 부드럽게 익히거나 잘게 다진 음식을 추천하세요
- 1회 식사량은 성인의 1/4~1/3 수준입니다
- 딱딱하거나 큰 덩어리 음식은 피해주세요"""
    elif child_age_months <= 30:
        food_guide = """이 아이는 유아식 단계입니다.
- 다양한 식감이 가능하지만 작게 자른 음식을 추천하세요
- 1회 식사량은 성인의 1/3~1/2 수준입니다
- 간은 살짝 싱겁게 조리해주세요"""
    elif child_age <= 3:
        food_guide = """이 아이는 유아식 완성기입니다.
- 대부분의 집밥 메뉴를 먹을 수 있지만 양을 줄여주세요
- 1회 식사량은 성인의 1/2 수준입니다"""
    else:
        food_guide = """이 아이는 3~5세 유아입니다.
- 일반 가정식을 먹을 수 있지만 양을 조절해주세요
- 1회 식사량은 성인의 1/2~2/3 수준입니다"""

    # 1인분 기준 중량 정보
    serving_ref = wiz.model("nutrition_api")
    age_group_key = '3~5세' if child_age >= 3 else '1~2세'
    sw = serving_ref.SERVING_WEIGHTS.get(age_group_key, {})
    serving_text = ", ".join([f"{k}={v}g" for k, v in sw.items()])

    system_instruction = f"""당신은 어린이 영양 전문가입니다. 부족 영양소를 채우는 가정식 저녁 메뉴를 추천합니다.
이 아이는 {age_detail_text}({age_group_key} 기준)입니다.
{food_guide}

반드시 아래 JSON 형식으로만 응답하세요.
{{"menus": [{{"name": "메뉴명", "description": "간단 설명", "nutrients": {{"calories": 0, "protein": 0, "fat": 0, "carbs": 0, "calcium": 0, "iron": 0}}, "reason": "추천 이유"}}], "tip": "간단한 조리 팁"}}
규칙:
- 알레르기 식품은 절대 포함 금지
- 내가 제공한 칼로리/영양소 수치를 절대 다시 계산하거나 추측하지 마세요
- 영양소 단위: calories=kcal, protein/fat/carbs=g, calcium/iron=mg
- 가정에서 쉽게 만들 수 있는 메뉴 2~3개 추천
- 부족한 영양소를 채우는 메뉴 우선
- 메뉴의 칼로리와 영양소는 반드시 아이 {age_detail_text}의 1인분 기준 ({age_group_key} 1인분 기준 중량: {serving_text})
- 추천 메뉴의 총 칼로리는 부족분을 넘지 않도록 하세요"""

    age_group = '3~5세' if child_age >= 3 else '1~2세'
    prompt = f"""{age_detail_text} 아이({age_group} 기준)의 오늘 어린이집 식사 영양 정보:
하루 전체 권장 섭취량: 칼로리 {daily_target['calories']}kcal, 단백질 {daily_target['protein']}g, 칼슘 {daily_target['calcium']}mg
어린이집 실제 섭취량: {consumed_text}
저녁에 보충 필요: {deficit_text}
{age_group} 어린이 1인분 기준 중량: {serving_text}

{allergy_text}
부족한 영양소를 보충할 수 있는 저녁 메뉴를 추천해주세요.
저녁 메뉴의 칼로리는 부족분({dinner_deficit.get('calories', 0)}kcal)에 맞춰주세요.
중요: 모든 영양소 수치는 반드시 {age_detail_text} 아이의 1인분 기준으로 계산해주세요."""

    stage3 = {'menus': [], 'tip': ''}
    try:
        gemini = _get_gemini()
        result = gemini.ask_json(prompt, system_instruction=system_instruction)
        if isinstance(result, dict) and 'menus' in result:
            stage3 = result
        else:
            stage3['tip'] = '저녁 메뉴 추천을 생성하지 못했습니다. 다시 시도해 주세요.'
            stage3['error'] = f"Gemini 응답 파싱 실패: {type(result).__name__}"
    except Exception as e:
        import traceback
        stage3['tip'] = '저녁 메뉴 추천 중 오류가 발생했습니다.'
        stage3['error'] = str(e)
        stage3['traceback'] = traceback.format_exc()

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
        gemini = _get_gemini()
        result = gemini.ask_json(prompt, system_instruction=system_instruction)
    except Exception as e:
        wiz.response.status(200, substitutes=[])
    if isinstance(result, list):
        wiz.response.status(200, substitutes=result)
    wiz.response.status(200, substitutes=[])
