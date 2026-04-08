# pyright: reportUndefinedVariable=false, reportMissingImports=false
import datetime
import json

Meals = wiz.model("db/childcheck/meals")
Children = wiz.model("db/childcheck/children")
ChildAllergies = wiz.model("db/childcheck/child_allergies")
AllergyCategories = wiz.model("db/childcheck/allergy_categories")
ServerMembers = wiz.model("db/login_db/server_members")
Users = wiz.model("db/login_db/users")
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

def _ai_analyze_all_meals(meal_foods, age_group, db_kcal, db_protein, child_age):
    """AI에게 전체 식단의 각 음식별 6대 영양소를 한 번에 추정 요청.
    DB의 칼로리/단백질을 앵커로, 어린이집 급식 목표를 가이드로 사용."""
    gemini = _get_gemini()

    # 연령별 목표 영양소 가져오기
    age_key = '3~5' if child_age >= 3 else '1~2'
    target = DAYCARE_TARGETS.get(age_key, DAYCARE_TARGET)

    # 끼니별 음식 목록 파싱
    parsed_meals = {}
    all_foods = []
    for mt, content in meal_foods.items():
        if not content:
            continue
        items = _parse_menu_names(content, age_group)
        food_names = [name for name, is_sub in items if not is_sub]
        sub_names = [name for name, is_sub in items if is_sub]
        parsed_meals[mt] = {'foods': food_names, 'substitutes': sub_names, 'items': items}
        all_foods.extend([(mt, name, is_sub) for name, is_sub in items])

    # AI 프롬프트 구성
    meals_desc = []
    for mt in ['오전간식', '점심', '오후간식']:
        if mt in parsed_meals:
            foods = parsed_meals[mt]['foods']
            subs = parsed_meals[mt]['substitutes']
            food_str = ', '.join(foods)
            if subs:
                food_str += f' (대체식: {", ".join(subs)})'
            meals_desc.append(f"- {mt}: {food_str}")

    meals_text = '\n'.join(meals_desc)

    constraint = ""
    # 6대 영양소 목표 텍스트 구성
    target_text = f"""어린이집 {age_group} 급식 일일 영양 목표 (보건복지부 기준):
  칼로리: {target.get('calories', 420)}kcal, 단백질: {target.get('protein', 11)}g, 지방: {target.get('fat', 17)}g
  탄수화물: {target.get('carbs', 73)}g, 칼슘: {target.get('calcium', 250)}mg, 철분: {target.get('iron', 3.3)}mg"""

    if db_kcal and db_protein:
        # 지방은 DB에 없으므로 목표값을 직접 사용
        t_fat = target.get('fat', 17)
        t_carbs = target.get('carbs', 73)
        t_calcium = target.get('calcium', 250)
        t_iron = target.get('iron', 3.3)
        constraint = f"""★★★ 필수 제약조건 (모든 수치 반드시 준수) ★★★
{target_text}

영양사 공식 수치 + 목표 기반 총합 (대체식 제외):
  총 칼로리 = {db_kcal}kcal (±10)
  총 단백질 = {db_protein}g (±1)
  총 지방 = {t_fat}g (±2)
  총 탄수화물 = {t_carbs}g (±5)
  총 칼슘 = {t_calcium}mg (±30)
  총 철분 = {t_iron}mg (±0.5)

⚠️ 지방 주의: 어린이집 급식은 참기름, 들기름, 식용유를 반찬 조리에 많이 사용합니다.
  - 볶음/무침류: 참기름·들기름 3~5g 추가
  - 조림류: 식용유 2~3g 추가
  - 국/탕류: 기름 1~2g 포함
  따라서 지방 총합이 {t_fat}g 수준이 됩니다. 지방을 과소 추정하지 마세요.

배분 순서:
1. 먼저 위 6가지 총합을 확보
2. 끼니별 배분 (오전간식 ~10%, 점심 ~60%, 오후간식 ~30%)
3. 끼니 내 각 음식에 배분
대체식은 총량 계산에서 제외합니다."""
    elif db_kcal:
        constraint = f"""★★★ 필수 제약조건 (반드시 준수) ★★★
{target_text}

이 식단의 영양사 공식 수치:
- 총 칼로리 = {db_kcal}kcal (±10kcal)

나머지 영양소도 위 목표에 근접하도록 배분하세요."""

    prompt = f"""어린이집 {age_group} 아이의 오늘 급식 식단입니다.
각 음식의 {age_group} 아이 1인분 기준 영양소를 추정해주세요.

식단:
{meals_text}

{constraint}

각 음식별로 아래 6대 영양소를 추정하세요:
- calories (kcal), protein (g), fat (g), carbs (g), calcium (mg), iron (mg)

이 식단은 시·구청 영양사가 6대 영양소 모두 목표에 맞춰 설계한 것입니다.
각 음식의 영양소를 합산하면 위 제약조건의 목표값에 근접해야 합니다.

반드시 아래 JSON 형식으로만 응답하세요:
{{
  "meals": {{
    "끼니이름": [
      {{"name": "음식이름", "calories": 0, "protein": 0, "fat": 0, "carbs": 0, "calcium": 0, "iron": 0, "category": "카테고리", "is_substitute": false}}
    ]
  }}
}}"""

    system = "당신은 한국 어린이집 급식 영양 분석 전문가입니다. 보건복지부 영유아 급식관리지침 기준으로 정확하게 영양소를 추정합니다. JSON만 응답하세요."

    result = gemini.ask_json(prompt, system_instruction=system)

    # 결과 파싱
    stage1_meals = []
    total = {k: 0.0 for k in DAYCARE_TARGET}

    if not isinstance(result, dict) or 'meals' not in result:
        print(f"[AI분석] 파싱 실패: {type(result)}")
        # fallback: 빈 결과
        for mt in ['오전간식', '점심', '오후간식']:
            if mt in parsed_meals:
                items = [{'name': n, 'calories': 0, 'protein': 0, 'fat': 0, 'carbs': 0, 'calcium': 0, 'iron': 0, 'source': 'error', 'is_substitute': is_sub, 'matched_name': n, 'category': '', 'serving_size': '1인분', 'serving_ratio': 1.0} for n, is_sub in parsed_meals[mt]['items']]
                stage1_meals.append({'meal_type': mt, 'items': items, 'subtotal': {k: 0 for k in DAYCARE_TARGET}})
        return {'meals': stage1_meals, 'total': total}

    ai_meals = result['meals']
    for mt in ['오전간식', '점심', '오후간식']:
        if mt not in parsed_meals:
            continue
        ai_items = ai_meals.get(mt, [])
        # AI 결과를 이름으로 매핑
        ai_map = {}
        for ai_item in ai_items:
            if isinstance(ai_item, dict):
                ai_map[ai_item.get('name', '')] = ai_item

        items = []
        sub_total = {k: 0.0 for k in DAYCARE_TARGET}
        for name, is_sub in parsed_meals[mt]['items']:
            ai_data = ai_map.get(name, {})
            item = {
                'name': name,
                'source': 'ai',
                'is_substitute': is_sub,
                'is_estimated': False,
                'matched_name': name,
                'serving_size': '1인분',
                'serving_ratio': 1.0,
                'category': ai_data.get('category', ''),
                'calories': round(float(ai_data.get('calories', 0)), 1),
                'protein': round(float(ai_data.get('protein', 0)), 1),
                'fat': round(float(ai_data.get('fat', 0)), 1),
                'carbs': round(float(ai_data.get('carbs', 0)), 1),
                'calcium': round(float(ai_data.get('calcium', 0)), 1),
                'iron': round(float(ai_data.get('iron', 0)), 1),
            }
            items.append(item)
            if not is_sub:
                for k in DAYCARE_TARGET:
                    sub_total[k] = round(sub_total[k] + item.get(k, 0), 1)

        stage1_meals.append({
            'meal_type': mt,
            'items': items,
            'subtotal': sub_total
        })
        for k in total:
            total[k] = round(total[k] + sub_total.get(k, 0), 1)

    # DB 앵커 보정: AI 합계가 DB 기준과 5% 이상 차이나면 비례 스케일링
    if db_kcal and db_kcal > 0 and total['calories'] > 0:
        cal_ratio = db_kcal / total['calories']
        prot_ratio = (db_protein / total['protein']) if (db_protein and total['protein'] > 0) else cal_ratio
        diff_pct = abs(1 - cal_ratio) * 100
        if diff_pct > 5:
            print(f"[AI분석] DB보정: AI={total['calories']}kcal vs DB={db_kcal}kcal ({diff_pct:.0f}% 차이) → 스케일링 적용")
            for meal_data in stage1_meals:
                sub = {k: 0.0 for k in DAYCARE_TARGET}
                for item in meal_data['items']:
                    if item.get('is_substitute'):
                        continue
                    item['calories'] = round(item['calories'] * cal_ratio, 1)
                    item['protein'] = round(item['protein'] * prot_ratio, 1)
                    item['fat'] = round(item['fat'] * cal_ratio, 1)
                    item['carbs'] = round(item['carbs'] * cal_ratio, 1)
                    item['calcium'] = round(item['calcium'] * cal_ratio, 1)
                    item['iron'] = round(item['iron'] * cal_ratio, 1)
                    for k in DAYCARE_TARGET:
                        sub[k] = round(sub[k] + item.get(k, 0), 1)
                meal_data['subtotal'] = sub
            # 합계 재계산
            total = {k: 0.0 for k in DAYCARE_TARGET}
            for meal_data in stage1_meals:
                for k in total:
                    total[k] = round(total[k] + meal_data['subtotal'].get(k, 0), 1)
            print(f"[AI분석] DB보정 후: {total}")

    # 목표 영양소 스케일링: 지방/탄수/칼슘/철분을 영양사 설계 목표값에 맞춤
    # DB에 칼로리/단백질만 있고 나머지 4종은 없으므로, 보건복지부 급식 목표를 기준으로 보정
    target_scale = {
        'fat': target.get('fat', 17),
        'carbs': target.get('carbs', 73),
        'calcium': target.get('calcium', 250),
        'iron': target.get('iron', 3.3),
    }
    scaled_any = False
    for nutrient, target_val in target_scale.items():
        if total.get(nutrient, 0) > 0 and target_val > 0:
            ratio = target_val / total[nutrient]
            if abs(1 - ratio) > 0.05:  # 5% 이상 차이
                scaled_any = True
                print(f"[AI분석] 목표보정 {nutrient}: AI={total[nutrient]} → 목표={target_val} (×{ratio:.2f})")
                for meal_data in stage1_meals:
                    for item in meal_data['items']:
                        if not item.get('is_substitute'):
                            item[nutrient] = round(item[nutrient] * ratio, 1)
                    meal_data['subtotal'][nutrient] = round(
                        sum(item[nutrient] for item in meal_data['items'] if not item.get('is_substitute')), 1)
                total[nutrient] = round(sum(m['subtotal'][nutrient] for m in stage1_meals), 1)
    if scaled_any:
        print(f"[AI분석] 최종: cal={total['calories']} prot={total['protein']} fat={total['fat']} carbs={total['carbs']} ca={total['calcium']} fe={total['iron']}")

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

            # 3. 기타 알레르기 키워드 텍스트 매칭
            for kw in other_keywords:
                if _keyword_in_content(kw, content):
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

    wiz.response.status(200, role=role,
        morning_snack=morning_snack, lunch=lunch, afternoon_snack=afternoon_snack,
        meal_allergy=meal_allergy, allergy_map=ALLERGY_MAP,
        allergy_warnings=allergy_warnings, allergy_dishes=allergy_dishes)

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

    # AI에게 전체 영양소 추정 요청
    stage1_result = _ai_analyze_all_meals(
        meal_foods, age_group, daily_total_kcal, daily_total_protein, child_age
    )

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
실제 섭취량: {consumed_text}
부족 영양소: {deficit_text}
{age_group} 어린이 1인분 기준 중량: {serving_text}

{allergy_text}
부족한 영양소를 보충할 수 있는 저녁 메뉴를 추천해주세요.
저녁 메뉴의 칼로리는 부족분({deficit.get('calories', 0)}kcal)에 맞춰주세요.
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
