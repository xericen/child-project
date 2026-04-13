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

# ===== 가이드라인 데이터 로드 (data/nutrition_guideline.json) =====
def _load_guideline():
    """프로젝트 data 폴더에서 가이드라인 JSON 로드"""
    _fs = wiz.project.fs("data")
    try:
        return _fs.read.json("nutrition_guideline.json", default={})
    except Exception:
        return {}

_GUIDELINE = _load_guideline()

# 식품군별 1회 분량 표준 영양값
FOOD_GROUP_STANDARDS = _GUIDELINE.get('food_group_standards', {
    '곡류': {'calories': 190, 'protein': 2.5, 'fat': 0.3, 'carbs': 44.0, 'calcium': 2.4, 'iron': 0.56},
    '고기류': {'calories': 50, 'protein': 5.0, 'fat': 2.0, 'carbs': 0.0, 'calcium': 11.1, 'iron': 1.17},
    '채소류': {'calories': 7, 'protein': 0.5, 'fat': 0.0, 'carbs': 1.5, 'calcium': 10.4, 'iron': 0.33},
    '국류': {'calories': 25, 'protein': 1.5, 'fat': 0.5, 'carbs': 2.0, 'calcium': 14.0, 'iron': 0.28},
    '김치류': {'calories': 3, 'protein': 0.3, 'fat': 0.0, 'carbs': 0.5, 'calcium': 6.6, 'iron': 0.11},
    '과일류': {'calories': 25, 'protein': 0.3, 'fat': 0.0, 'carbs': 6.0, 'calcium': 2.0, 'iron': 0.10},
    '우유': {'calories': 120, 'protein': 6.4, 'fat': 6.0, 'carbs': 9.2, 'calcium': 210.0, 'iron': 0.20},
    '요구르트': {'calories': 77, 'protein': 2.6, 'fat': 2.0, 'carbs': 12.0, 'calcium': 124.5, 'iron': 0.37},
})

# 연령별 × 끼니별 식품군 제공 횟수 (가이드라인 표 9)
MEAL_SERVING_COUNTS = _GUIDELINE.get('meal_serving_counts', {
    '1~2세': {
        '점심': {'곡류': 0.7, '고기류': 1.5, '채소류': 1.5, '국류': 1.0, '김치류': 1.0, '과일류': 0.0, '우유': 0.0, '요구르트': 0.0},
        '간식': {'곡류': 0.3, '고기류': 0.0, '채소류': 0.0, '국류': 0.0, '김치류': 0.0, '과일류': 1.0, '우유': 1.0, '요구르트': 1.0},
    },
    '3~5세': {
        '점심': {'곡류': 1.0, '고기류': 2.0, '채소류': 2.5, '국류': 1.0, '김치류': 1.0, '과일류': 0.0, '우유': 0.0, '요구르트': 0.0},
        '간식': {'곡류': 0.5, '고기류': 0.0, '채소류': 0.0, '국류': 0.0, '김치류': 0.0, '과일류': 1.5, '우유': 1.0, '요구르트': 1.0},
    },
})

# 과일명 목록 (식품군 분류용)
_FRUIT_KEYWORDS = [
    '사과', '배', '바나나', '딸기', '수박', '포도', '귤', '오렌지', '키위',
    '골드키위', '토마토', '방울토마토', '한라봉', '파인애플', '참외', '복숭아',
    '자두', '감', '망고', '블루베리', '멜론', '체리', '앵두', '살구', '레몬',
    '라임', '자몽', '석류', '무화과', '매실',
]

def _classify_food_group(name):
    """음식명 → 식품군 분류 (룰 기반, 결정적)
    가이드라인 식품군: 곡류 / 고기류 / 채소류 / 국류 / 김치류 / 과일류 / 우유 / 요구르트"""
    # 우유 (정확히 우유)
    if '우유' in name and '두유' not in name:
        return '우유'
    # 요구르트
    if any(kw in name for kw in ['요구르트', '요거트', '유산균']):
        return '요구르트'
    # 치즈, 두유 → 우유류 대용
    if any(kw in name for kw in ['치즈', '밀크', '두유']):
        return '우유'
    # 과일류
    if any(f in name for f in _FRUIT_KEYWORDS):
        return '과일류'
    # 김치류 (국/찌개보다 먼저 체크)
    if any(kw in name for kw in ['김치', '깍두기', '피클', '장아찌']):
        return '김치류'
    # 국/찌개/탕/스프
    if any(kw in name for kw in ['국', '찌개', '탕', '스프']):
        return '국류'
    # 고기·생선·계란·콩류
    if any(kw in name for kw in [
        '고기', '볶음', '조림', '구이', '튀김', '까스', '돈까스', '돈가스',
        '너겟', '치킨', '불고기', '갈비', '제육', '탕수육', '소시지', '햄',
        '베이컨', '닭', '돼지', '소고기', '쇠고기', '생선', '계란', '달걀',
        '두부', '오믈렛', '스크램블', '만두', '어묵', '장조림', '수육',
        '떡갈비', '미트볼', '카레', '커틀릿', '스테이크', '전', '부침',
        '콩', '멸치', '새우', '오징어', '조개', '굴', '꽃게', '찜',
        '동그랑땡', '완자', '탕수', '꼬치', '까스',
    ]):
        return '고기류'
    # 곡류
    if any(kw in name for kw in [
        '밥', '죽', '면', '국수', '빵', '식빵', '토스트', '시리얼',
        '감자', '고구마', '떡', '수제비', '파스타', '라면', '우동',
        '주먹밥', '볶음밥', '비빔밥', '잡곡', '현미', '쌀', '백설기',
        '롤빵', '모닝빵',
    ]):
        return '곡류'
    # 채소류 (나물, 무침 등)
    if any(kw in name for kw in [
        '나물', '무침', '샐러드', '쌈', '채소', '야채',
        '오이', '당근', '시금치', '콩나물', '숙주', '연근',
    ]):
        return '채소류'
    # 기본 fallback → 채소류
    return '채소류'


def _get_meal_category(meal_type):
    """끼니 유형 → '점심' 또는 '간식' (제공횟수 테이블 키)"""
    if meal_type == '점심':
        return '점심'
    return '간식'


def _ai_analyze_all_meals(meal_foods, age_group, db_kcal, db_protein, child_age):
    """하이브리드 영양 분석 (결정적 결과).
    1순위: 로컬 식품 DB exact match → 정확한 영양값
    2순위: BASIC_INGREDIENTS 사전 매칭
    3순위: 식품군 표준값 × 제공횟수 (가이드라인 기준)
    - 총합 칼로리/단백질: DB값 사용, 개별 아이템은 비례 보정"""

    print(f"[영양분석] ===== 하이브리드 분석 시작 (DB→기본재료→식품군) =====")
    print(f"[영양분석] 연령그룹: {age_group}, 나이: {child_age}세")
    print(f"[영양분석] 식단표 등록값 → 열량: {db_kcal}kcal, 단백질: {db_protein}g")

    age_key = '3~5세' if child_age >= 3 else '1~2세'
    serving_table = MEAL_SERVING_COUNTS[age_key]

    # 식품군별 1인1회 배식량 (g) — 가이드라인 기준
    _SERVING_GRAMS = {
        '1~2세': {'곡류': 90, '고기류': 30, '채소류': 30, '국류': 100, '김치류': 14, '과일류': 50, '우유': 200, '요구르트': 100},
        '3~5세': {'곡류': 130, '고기류': 45, '채소류': 40, '국류': 140, '김치류': 20, '과일류': 80, '우유': 200, '요구르트': 100},
    }
    serving_grams = _SERVING_GRAMS.get(age_key, _SERVING_GRAMS['1~2세'])

    # 로컬 영양 DB 로드 (API/AI 호출 없이 결정적 결과)
    try:
        _napi = wiz.model("nutrition_api")
    except Exception:
        _napi = None

    all_items_by_meal = {}

    for mt in ['오전간식', '점심', '오후간식']:
        content = meal_foods.get(mt, '')
        if not content:
            continue

        menu_items = _parse_menu_names(content, age_group)
        meal_cat = _get_meal_category(mt)
        serving_counts = serving_table[meal_cat]

        # 1단계: 각 음식을 식품군으로 분류
        classified = []
        for name, is_substitute in menu_items:
            group = _classify_food_group(name)
            classified.append((name, is_substitute, group))

        # 2단계: 같은 끼니 내 식품군별 음식 수 카운트 (대체식 제외)
        group_counts = {}
        for name, is_sub, group in classified:
            if not is_sub:
                group_counts[group] = group_counts.get(group, 0) + 1

        # 3단계: 하이브리드 — 로컬DB 우선, 없으면 식품군 표준값
        items = []
        for name, is_substitute, group in classified:
            std = FOOD_GROUP_STANDARDS[group]
            total_servings = serving_counts.get(group, 0.0)
            n_foods = group_counts.get(group, 1)

            if is_substitute or total_servings <= 0:
                servings_per_food = 1.0
            else:
                servings_per_food = total_servings / n_foods

            # 하이브리드: 로컬 DB에서 검색 시도
            local_result = None
            local_source = None
            if _napi and not is_substitute:
                try:
                    local_result, local_source = _napi.search_local(name)
                except Exception:
                    pass

            if local_result and local_source:
                # DB 결과 사용 (per 100g → 배식량 기준 스케일)
                sg = serving_grams.get(group, 50)
                scale = (sg / 100.0) * servings_per_food
                item = {
                    'name': name,
                    'source': local_source,
                    'is_substitute': is_substitute,
                    'is_estimated': False,
                    'matched_name': local_result.get('name', name),
                    'serving_size': f'{servings_per_food:.1f}회({sg}g)',
                    'serving_ratio': round(servings_per_food, 2),
                    'category': group,
                    'calories': round(float(local_result.get('calories', 0)) * scale, 1),
                    'protein': round(float(local_result.get('protein', 0)) * scale, 1),
                    'fat': round(float(local_result.get('fat', 0)) * scale, 1),
                    'carbs': round(float(local_result.get('carbohydrate', local_result.get('carbs', 0))) * scale, 1),
                    'calcium': round(float(local_result.get('calcium', 0)) * scale, 1),
                    'iron': round(float(local_result.get('iron', 0)) * scale, 1),
                }
                print(f"[분석] {mt}: {name} → {group}({local_source}, matched={item['matched_name']}) ×{scale:.2f} cal={item['calories']}kcal")
            else:
                # 식품군 표준값 사용 (기존 방식)
                item = {
                    'name': name,
                    'source': 'food_group',
                    'is_substitute': is_substitute,
                    'is_estimated': False,
                    'matched_name': name,
                    'serving_size': f'{servings_per_food:.1f}회',
                    'serving_ratio': round(servings_per_food, 2),
                    'category': group,
                    'calories': round(std['calories'] * servings_per_food, 1),
                    'protein': round(std['protein'] * servings_per_food, 1),
                    'fat': round(std['fat'] * servings_per_food, 1),
                    'carbs': round(std['carbs'] * servings_per_food, 1),
                    'calcium': round(std['calcium'] * servings_per_food, 1),
                    'iron': round(std['iron'] * servings_per_food, 1),
                }
                print(f"[분석] {mt}: {name} → {group}(food_group) ×{servings_per_food:.1f}회 cal={item['calories']}kcal")

            items.append(item)

        all_items_by_meal[mt] = items

    # ── 식품군×제공횟수 기준 합계 (대체식 제외) ──
    raw_total_cal = 0.0
    raw_total_prot = 0.0
    total_calcium = 0.0
    total_iron = 0.0
    total_fat = 0.0
    total_carbs = 0.0
    for mt_items in all_items_by_meal.values():
        for item in mt_items:
            if not item['is_substitute']:
                raw_total_cal += item['calories']
                raw_total_prot += item['protein']
                total_calcium += item['calcium']
                total_iron += item['iron']
                total_fat += item['fat']
                total_carbs += item['carbs']

    print(f"[영양분석] 식품군합계={round(raw_total_cal, 1)}kcal, DB값={db_kcal}kcal, 비율={round(float(db_kcal or 0) / raw_total_cal, 2) if raw_total_cal > 0 else 'N/A'}")

    # ── 칼로리/단백질: DB값에 맞춰 개별 아이템 비례 보정 ──
    cal_ratio = 1.0
    prot_ratio = 1.0
    if db_kcal and db_kcal > 0 and raw_total_cal > 0:
        cal_ratio = float(db_kcal) / raw_total_cal
        if cal_ratio < 0.3 or cal_ratio > 3.0:
            print(f"[영양분석] ⚠️ 열량 스케일 비율 이상: ×{cal_ratio:.3f} (식품군합계={round(raw_total_cal, 1)}, DB={db_kcal})")
        else:
            print(f"[영양분석] 열량 스케일: ×{cal_ratio:.3f}")
    if db_protein and db_protein > 0 and raw_total_prot > 0:
        prot_ratio = float(db_protein) / raw_total_prot
        if prot_ratio < 0.3 or prot_ratio > 3.0:
            print(f"[영양분석] ⚠️ 단백질 스케일 비율 이상: ×{prot_ratio:.3f}")
        else:
            print(f"[영양분석] 단백질 스케일: ×{prot_ratio:.3f}")

    for mt_items in all_items_by_meal.values():
        for item in mt_items:
            if not item['is_substitute']:
                item['calories'] = round(item['calories'] * cal_ratio, 1)
                item['protein'] = round(item['protein'] * prot_ratio, 1)

    # ── 결과 조립 ──
    final_cal = float(db_kcal) if db_kcal and db_kcal > 0 else round(raw_total_cal, 1)
    final_prot = float(db_protein) if db_protein and db_protein > 0 else round(raw_total_prot, 1)

    total = {
        'calories': final_cal,
        'protein': final_prot,
        'fat': round(total_fat, 1),
        'carbs': round(total_carbs, 1),
        'calcium': round(total_calcium, 1),
        'iron': round(total_iron, 1),
    }

    stage1_meals = []
    for mt in ['오전간식', '점심', '오후간식']:
        items = all_items_by_meal.get(mt, [])
        if not items:
            continue
        sub_total = {'calories': 0.0, 'protein': 0.0, 'fat': 0.0, 'carbs': 0.0, 'calcium': 0.0, 'iron': 0.0}
        for item in items:
            if not item['is_substitute']:
                for k in sub_total:
                    sub_total[k] = round(sub_total[k] + item.get(k, 0), 1)
        stage1_meals.append({
            'meal_type': mt,
            'items': items,
            'subtotal': sub_total
        })

    print(f"[영양분석] ===== 최종 결과 =====")
    print(f"[영양분석] cal={total['calories']}kcal prot={total['protein']}g fat={total['fat']}g carbs={total['carbs']}g ca={total['calcium']}mg fe={total['iron']}mg")

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

    # DB 저장 총 칼로리/단백질 (HWP 업로드 값)
    db_total_kcal = None
    db_total_protein = None
    child_age_for_db = child_age_for_kcal
    for m in meals:
        if child_age_for_db >= 3:
            if m.get('kcal_35'):
                db_total_kcal = m['kcal_35']
            if m.get('protein_35'):
                db_total_protein = m['protein_35']
        else:
            if m.get('kcal'):
                db_total_kcal = m['kcal']
            if m.get('protein'):
                db_total_protein = m['protein']

    wiz.response.status(200, role=role,
        morning_snack=morning_snack, lunch=lunch, afternoon_snack=afternoon_snack,
        meal_allergy=meal_allergy, allergy_map=ALLERGY_MAP,
        allergy_warnings=allergy_warnings, allergy_dishes=allergy_dishes,
        meal_kcal=meal_kcal,
        db_kcal=db_total_kcal, db_protein=db_total_protein)

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

    # ── 식품군 기반 영양 분석 (결정적, API/AI 미사용) ──
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
        ratio = abs(diff) / target[k] if target[k] > 0 else 0
        if diff < 0 and ratio > 0.3:
            # 30% 이상 부족할 때만 '부족'
            deficit[k] = round(abs(diff), 1)
            surplus[k] = 0
            status[k] = '부족'
        elif diff > 0 and ratio > 0.3:
            # 30% 이상 초과할 때만 '초과'
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

    # 연령별 단일 메뉴 칼로리 합리 범위
    if child_age >= 3:
        per_item_min, per_item_max = 40, 500  # 3~5세
    else:
        per_item_min, per_item_max = 30, 350  # 1~2세
    deficit_kcal = dinner_deficit.get('calories', 0)

    def _verify_dinner(result):
        """저녁 추천 결과 검증. (ok, issues) 반환"""
        issues = []
        if not isinstance(result, dict) or 'menus' not in result:
            return False, ['응답 형식 오류']
        menus = result['menus']
        if not menus:
            return False, ['추천 메뉴 없음']
        total_kcal = 0
        for m in menus:
            nut = m.get('nutrients', {})
            cal = nut.get('calories', 0)
            total_kcal += cal
            if cal < per_item_min or cal > per_item_max:
                issues.append(f"{m.get('name','?')}: {cal}kcal (범위 {per_item_min}~{per_item_max})")
        if deficit_kcal > 0:
            ratio = total_kcal / deficit_kcal
            if ratio < 0.5 or ratio > 1.5:
                issues.append(f"총 {total_kcal}kcal vs 부족분 {deficit_kcal}kcal (비율 {ratio:.1f})")
        return len(issues) == 0, issues

    def _ask_gemini(p, si):
        gemini = _get_gemini()
        return gemini.ask_json(p, system_instruction=si)

    try:
        result = _ask_gemini(prompt, system_instruction)
        if isinstance(result, dict) and 'menus' in result:
            ok, issues = _verify_dinner(result)
            if ok:
                stage3 = result
                stage3['verified'] = True
                print(f"[Stage3] 검증 통과")
            else:
                print(f"[Stage3] 검증 실패 (1차): {issues}")
                # 보정 프롬프트로 재시도 (최대 1회)
                retry_prompt = prompt + f"\n\n[주의] 이전 답변의 문제: {'; '.join(issues)}\n수정해서 다시 답변해주세요."
                try:
                    result2 = _ask_gemini(retry_prompt, system_instruction)
                    if isinstance(result2, dict) and 'menus' in result2:
                        ok2, issues2 = _verify_dinner(result2)
                        if ok2:
                            stage3 = result2
                            stage3['verified'] = True
                            print(f"[Stage3] 재시도 검증 통과")
                        else:
                            print(f"[Stage3] 재시도 검증 실패: {issues2}")
                            stage3 = result2
                            stage3['verified'] = False
                            stage3['verification_issues'] = issues2
                    else:
                        stage3 = result
                        stage3['verified'] = False
                        stage3['verification_issues'] = issues
                except Exception:
                    stage3 = result
                    stage3['verified'] = False
                    stage3['verification_issues'] = issues
        else:
            stage3['tip'] = '저녁 메뉴 추천을 생성하지 못했습니다. 다시 시도해 주세요.'
            stage3['error'] = f"Gemini 응답 파싱 실패: {type(result).__name__}"
            stage3['verified'] = False
    except Exception as e:
        import traceback
        stage3['tip'] = '저녁 메뉴 추천 중 오류가 발생했습니다.'
        stage3['error'] = str(e)
        stage3['traceback'] = traceback.format_exc()
        stage3['verified'] = False

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
