import urllib.request
import urllib.parse
import json
import re
import time
import threading
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

API_BASE = 'https://apis.data.go.kr/1471000/FoodNtrCpntDbInfo02/getFoodNtrCpntDbInq02'
# 메뉴젠 API (복합조리식 전용)
API_BASE_MENUGEN = 'https://apis.data.go.kr/1471000/FoodNtrCpntDbInfo01/getFoodNtrCpntDbInq01'
API_KEY = os.environ.get('FOOD_SAFETY_API_KEY', '')

# AMT_NUM 필드 매핑 (식약처 API 표준, per 100g)
NUTRIENT_FIELDS = {
    'calories': ('AMT_NUM1', 'kcal'),
    'protein': ('AMT_NUM3', 'g'),
    'fat': ('AMT_NUM4', 'g'),
    'carbohydrate': ('AMT_NUM6', 'g'),
    'sugar': ('AMT_NUM7', 'g'),
    'fiber': ('AMT_NUM8', 'g'),
    'calcium': ('AMT_NUM9', 'mg'),
    'iron': ('AMT_NUM10', 'mg'),
    'phosphorus': ('AMT_NUM11', 'mg'),
    'potassium': ('AMT_NUM12', 'mg'),
    'sodium': ('AMT_NUM13', 'mg'),
    'vitamin_a': ('AMT_NUM14', 'μg RAE'),
    'vitamin_c': ('AMT_NUM16', 'mg'),
}

NUTRIENT_LABELS = {
    'calories': '열량',
    'protein': '단백질',
    'fat': '지방',
    'carbohydrate': '탄수화물',
    'sugar': '당류',
    'fiber': '식이섬유',
    'calcium': '칼슘',
    'iron': '철분',
    'phosphorus': '인',
    'potassium': '칼륨',
    'sodium': '나트륨',
    'vitamin_a': '비타민A',
    'vitamin_c': '비타민C',
}

# 알레르기 표기 등 제거용 패턴
CLEAN_PATTERN = re.compile(r'[ⓢⓄ①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳\d.]')

# green 마커 패턴
GREEN_PATTERN = re.compile(r'\{\{green:.*?\}\}')

# ===== 어린이집 급식 영양 기준 (공유 상수) =====

# 연령별 하루 에너지 필요량 (kcal)
DAILY_ENERGY = {
    '1~2세': 1000,
    '3~5세': 1400,
}

# 끼니별 하루 에너지 대비 비율
MEAL_RATIOS = {
    '오전간식': 0.10,
    '점심': 0.35,
    '오후간식': 0.10,
    '기타': 0.10,
}

# 어린이집 제공분(점심+간식2회) 하루 영양 목표 — 하루의 ~50%
DAYCARE_TARGETS = {
    '1~2세': {
        'calories': {'value': 420, 'label': '420kcal', 'unit': 'kcal'},
        'protein': {'value': 20, 'label': '20g', 'unit': 'g'},
        'fat': {'value': 17, 'label': '17g', 'unit': 'g'},
        'carbohydrate': {'value': 73, 'label': '73g', 'unit': 'g'},
        'calcium': {'value': 250, 'label': '250mg', 'unit': 'mg'},
        'iron': {'value': 3.3, 'label': '3.3mg', 'unit': 'mg'},
    },
    '3~5세': {
        'calories': {'value': 640, 'label': '640kcal', 'unit': 'kcal'},
        'protein': {'value': 12.5, 'label': '12.5g', 'unit': 'g'},
        'fat': {'value': 23, 'label': '23g', 'unit': 'g'},
        'carbohydrate': {'value': 102, 'label': '102g', 'unit': 'g'},
        'calcium': {'value': 275, 'label': '275mg', 'unit': 'mg'},
        'iron': {'value': 4.5, 'label': '4.5mg', 'unit': 'mg'},
    },
}

DISPLAY_NAMES = {
    'calories': '열량',
    'protein': '단백질',
    'fat': '지방',
    'carbohydrate': '탄수화물',
    'calcium': '칼슘',
    'iron': '철분',
}

# 연령별 × 음식 카테고리별 1인분 기준 중량(g) — 보건복지부 어린이집 급식관리지침 참고
SERVING_WEIGHTS = {
    '1~2세': {
        '밥류': 80, '국 및 탕류': 120, '나물·숙채류': 40, '볶음류': 40,
        '구이류': 40, '찜류': 40, '조림류': 30, '튀김류': 30,
        '과일류': 50, '유제품': 100, '빵 및 과자류': 30, '기타': 50,
    },
    '3~5세': {
        '밥류': 120, '국 및 탕류': 150, '나물·숙채류': 50, '볶음류': 50,
        '구이류': 50, '찜류': 50, '조림류': 40, '튀김류': 40,
        '과일류': 80, '유제품': 150, '빵 및 과자류': 40, '기타': 60,
    },
}

# 간단한 식재료 기본 영양소 (per 100g, 식약처 식품성분표 기준)
# ===== 연령별 메뉴 분기 =====
# 식단표에서 연령별로 다른 메뉴가 공백 없이 이어붙어 있는 경우 (1~2세 메뉴, 3~5세 메뉴)
AGE_MENU_PAIRS = [
    ('백김치', '배추김치'),
]
BASIC_INGREDIENTS = {
    '바나나': {'name': '바나나', 'serving_size': '100g', 'category': '과일류', 'calories': 93, 'protein': 1.0, 'fat': 0.1, 'carbohydrate': 23.5, 'sugar': 15.0, 'fiber': 2.6, 'calcium': 4, 'iron': 0.3, 'phosphorus': 28, 'potassium': 380, 'sodium': 1, 'vitamin_a': 4, 'vitamin_c': 10},
    '우유': {'name': '우유', 'serving_size': '200ml', 'category': '유제품', 'calories': 65, 'protein': 3.2, 'fat': 3.7, 'carbohydrate': 4.6, 'sugar': 4.6, 'fiber': 0, 'calcium': 113, 'iron': 0, 'phosphorus': 92, 'potassium': 150, 'sodium': 41, 'vitamin_a': 40, 'vitamin_c': 1},
    '사과': {'name': '사과', 'serving_size': '100g', 'category': '과일류', 'calories': 57, 'protein': 0.2, 'fat': 0.1, 'carbohydrate': 14.8, 'sugar': 12.0, 'fiber': 1.7, 'calcium': 4, 'iron': 0.1, 'phosphorus': 10, 'potassium': 110, 'sodium': 0, 'vitamin_a': 2, 'vitamin_c': 3},
    '딸기': {'name': '딸기', 'serving_size': '100g', 'category': '과일류', 'calories': 35, 'protein': 0.8, 'fat': 0.2, 'carbohydrate': 8.3, 'sugar': 5.5, 'fiber': 1.8, 'calcium': 17, 'iron': 0.4, 'phosphorus': 28, 'potassium': 195, 'sodium': 2, 'vitamin_a': 0, 'vitamin_c': 67},
    '귤': {'name': '귤', 'serving_size': '100g', 'category': '과일류', 'calories': 44, 'protein': 0.8, 'fat': 0.1, 'carbohydrate': 11.0, 'sugar': 8.5, 'fiber': 1.4, 'calcium': 15, 'iron': 0.1, 'phosphorus': 15, 'potassium': 150, 'sodium': 2, 'vitamin_a': 40, 'vitamin_c': 44},
    '수박': {'name': '수박', 'serving_size': '100g', 'category': '과일류', 'calories': 31, 'protein': 0.5, 'fat': 0.1, 'carbohydrate': 7.6, 'sugar': 6.0, 'fiber': 0.3, 'calcium': 3, 'iron': 0.2, 'phosphorus': 8, 'potassium': 102, 'sodium': 2, 'vitamin_a': 30, 'vitamin_c': 6},
    '포도': {'name': '포도', 'serving_size': '100g', 'category': '과일류', 'calories': 60, 'protein': 0.5, 'fat': 0.2, 'carbohydrate': 15.5, 'sugar': 14.0, 'fiber': 0.5, 'calcium': 5, 'iron': 0.3, 'phosphorus': 13, 'potassium': 150, 'sodium': 1, 'vitamin_a': 2, 'vitamin_c': 2},
    '요구르트': {'name': '요구르트', 'serving_size': '100g', 'category': '유제품', 'calories': 80, 'protein': 3.3, 'fat': 2.0, 'carbohydrate': 12.0, 'sugar': 10.0, 'fiber': 0, 'calcium': 120, 'iron': 0, 'phosphorus': 95, 'potassium': 155, 'sodium': 50, 'vitamin_a': 12, 'vitamin_c': 1},
    '치즈': {'name': '치즈', 'serving_size': '100g', 'category': '유제품', 'calories': 310, 'protein': 23.0, 'fat': 24.0, 'carbohydrate': 1.5, 'sugar': 0.5, 'fiber': 0, 'calcium': 600, 'iron': 0.3, 'phosphorus': 430, 'potassium': 75, 'sodium': 640, 'vitamin_a': 260, 'vitamin_c': 0},
    '식빵': {'name': '식빵', 'serving_size': '100g', 'category': '곡류', 'calories': 274, 'protein': 9.0, 'fat': 3.6, 'carbohydrate': 50.0, 'sugar': 5.0, 'fiber': 2.5, 'calcium': 40, 'iron': 1.0, 'phosphorus': 90, 'potassium': 100, 'sodium': 500, 'vitamin_a': 0, 'vitamin_c': 0},
    '쌀밥': {'name': '쌀밥', 'serving_size': '100g', 'category': '곡류', 'calories': 149, 'protein': 2.6, 'fat': 0.3, 'carbohydrate': 34.0, 'sugar': 0, 'fiber': 0.3, 'calcium': 2, 'iron': 0.1, 'phosphorus': 28, 'potassium': 26, 'sodium': 2, 'vitamin_a': 0, 'vitamin_c': 0},
    '백미밥': {'name': '백미밥', 'serving_size': '100g', 'category': '곡류', 'calories': 149, 'protein': 2.6, 'fat': 0.3, 'carbohydrate': 34.0, 'sugar': 0, 'fiber': 0.3, 'calcium': 2, 'iron': 0.1, 'phosphorus': 28, 'potassium': 26, 'sodium': 2, 'vitamin_a': 0, 'vitamin_c': 0},
    '배': {'name': '배', 'serving_size': '100g', 'category': '과일류', 'calories': 45, 'protein': 0.3, 'fat': 0.2, 'carbohydrate': 11.9, 'sugar': 8.4, 'fiber': 1.5, 'calcium': 4, 'iron': 0.1, 'phosphorus': 8, 'potassium': 125, 'sodium': 0, 'vitamin_a': 0, 'vitamin_c': 3},
    '오렌지': {'name': '오렌지', 'serving_size': '100g', 'category': '과일류', 'calories': 47, 'protein': 1.0, 'fat': 0.1, 'carbohydrate': 11.0, 'sugar': 8.0, 'fiber': 2.4, 'calcium': 40, 'iron': 0.1, 'phosphorus': 20, 'potassium': 180, 'sodium': 1, 'vitamin_a': 10, 'vitamin_c': 43},
    '키위': {'name': '키위', 'serving_size': '100g', 'category': '과일류', 'calories': 61, 'protein': 1.1, 'fat': 0.5, 'carbohydrate': 14.7, 'sugar': 9.0, 'fiber': 2.5, 'calcium': 25, 'iron': 0.3, 'phosphorus': 30, 'potassium': 290, 'sodium': 3, 'vitamin_a': 3, 'vitamin_c': 72},
    '골드키위': {'name': '골드키위', 'serving_size': '100g', 'category': '과일류', 'calories': 63, 'protein': 1.0, 'fat': 0.3, 'carbohydrate': 15.4, 'sugar': 10.0, 'fiber': 1.4, 'calcium': 20, 'iron': 0.2, 'phosphorus': 25, 'potassium': 315, 'sodium': 3, 'vitamin_a': 3, 'vitamin_c': 105},
    '토마토': {'name': '토마토', 'serving_size': '100g', 'category': '과일류', 'calories': 14, 'protein': 0.7, 'fat': 0.1, 'carbohydrate': 3.0, 'sugar': 2.6, 'fiber': 0.8, 'calcium': 7, 'iron': 0.3, 'phosphorus': 20, 'potassium': 210, 'sodium': 4, 'vitamin_a': 50, 'vitamin_c': 11},
    '방울토마토': {'name': '방울토마토', 'serving_size': '100g', 'category': '과일류', 'calories': 16, 'protein': 0.8, 'fat': 0.2, 'carbohydrate': 3.3, 'sugar': 3.0, 'fiber': 1.0, 'calcium': 9, 'iron': 0.3, 'phosphorus': 22, 'potassium': 230, 'sodium': 5, 'vitamin_a': 55, 'vitamin_c': 15},
    '한라봉': {'name': '한라봉', 'serving_size': '100g', 'category': '과일류', 'calories': 47, 'protein': 0.8, 'fat': 0.1, 'carbohydrate': 11.6, 'sugar': 9.0, 'fiber': 1.2, 'calcium': 20, 'iron': 0.1, 'phosphorus': 15, 'potassium': 165, 'sodium': 1, 'vitamin_a': 30, 'vitamin_c': 50},
    '파인애플': {'name': '파인애플', 'serving_size': '100g', 'category': '과일류', 'calories': 46, 'protein': 0.5, 'fat': 0.1, 'carbohydrate': 11.8, 'sugar': 10.0, 'fiber': 1.0, 'calcium': 15, 'iron': 0.3, 'phosphorus': 8, 'potassium': 130, 'sodium': 1, 'vitamin_a': 3, 'vitamin_c': 15},
}


class NutritionAPI:
    # 모듈 상수를 인스턴스에서 접근 가능하도록 클래스 속성으로 참조
    DAYCARE_TARGETS = DAYCARE_TARGETS
    DAILY_ENERGY = DAILY_ENERGY
    MEAL_RATIOS = MEAL_RATIOS
    DISPLAY_NAMES = DISPLAY_NAMES
    SERVING_WEIGHTS = SERVING_WEIGHTS

    def __init__(self):
        self._cache = {}
        self._cache_ttl = 86400  # 24시간
        self._lock = threading.Lock()
        self._disk_cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'nutrition_cache.json')
        self._load_disk_cache()
        self._NutritionMapping = None
        self._NutritionFoods = None

    def _get_mapping_model(self):
        """DB 매핑 모델을 지연 로딩 (wiz 컨텍스트 필요)"""
        if self._NutritionMapping is None:
            try:
                self._NutritionMapping = wiz.model("db/childcheck/nutrition_mapping")
            except Exception:
                pass
        return self._NutritionMapping

    def _get_foods_model(self):
        """로컬 영양 DB 모델을 지연 로딩"""
        if self._NutritionFoods is None:
            try:
                self._NutritionFoods = wiz.model("db/childcheck/nutrition_foods")
            except Exception:
                pass
        return self._NutritionFoods

    def _db_mapping_get(self, menu_name):
        """DB 매핑 캐시에서 조회"""
        NM = self._get_mapping_model()
        if NM is None:
            return None
        try:
            row = NM.get_or_none(NM.menu_name == menu_name)
            if row and row.nutrients:
                return json.loads(row.nutrients)
        except Exception:
            pass
        return None

    def _db_mapping_save(self, menu_name, result, food_code=None, food_name=None, source='api'):
        """DB 매핑 캐시에 저장"""
        NM = self._get_mapping_model()
        if NM is None:
            return
        try:
            nutrients_json = json.dumps(result, ensure_ascii=False) if result else None
            # upsert: 있으면 업데이트, 없으면 삽입
            existing = NM.get_or_none(NM.menu_name == menu_name)
            if existing:
                NM.update(
                    food_code=food_code,
                    food_name=food_name,
                    source=source,
                    nutrients=nutrients_json
                ).where(NM.menu_name == menu_name).execute()
            else:
                NM.create(
                    menu_name=menu_name,
                    food_code=food_code,
                    food_name=food_name,
                    source=source,
                    nutrients=nutrients_json
                )
        except Exception:
            pass

    def _db_search(self, menu_name):
        """로컬 nutrition_foods DB에서 LIKE 검색 후 최적 후보 선택"""
        NF = self._get_foods_model()
        if NF is None:
            return None
        try:
            import peewee as pw
            # 1차: 정확 매칭
            exact = NF.select().where(NF.food_name == menu_name).first()
            if exact:
                return self._foods_row_to_nutrient(exact)

            # 2차: LIKE 검색 (앞뒤 와일드카드, 짧은 이름 우선)
            candidates = list(NF.select().where(
                NF.food_name.contains(menu_name)
            ).order_by(pw.fn.CHAR_LENGTH(NF.food_name)).limit(30))

            # 3차: 메뉴명이 검색어를 포함하는 경우 (역방향)
            if not candidates and len(menu_name) >= 2:
                # 원재료명 추출 후 재검색
                base = self._extract_base_ingredient(menu_name)
                if base != menu_name and len(base) >= 2:
                    candidates = list(NF.select().where(
                        NF.food_name.contains(base)
                    ).order_by(pw.fn.CHAR_LENGTH(NF.food_name)).limit(30))

            if not candidates:
                return None

            # 후보 중 최적 선택 (기존 _score_match 로직 활용)
            best = None
            best_score = float('inf')
            for row in candidates:
                score = self._score_foods_match(menu_name, row)
                if score < best_score:
                    best_score = score
                    best = row

            if best is not None:
                return self._foods_row_to_nutrient(best)
        except Exception:
            pass
        return None

    def _foods_row_to_nutrient(self, row):
        """nutrition_foods DB 행을 영양소 dict로 변환"""
        return {
            'name': row.food_name,
            'serving_size': row.serving_size or '100g',
            'category': row.category or '',
            'calories': float(row.calories or 0),
            'protein': float(row.protein or 0),
            'fat': float(row.fat or 0),
            'carbohydrate': float(row.carbohydrate or 0),
            'sugar': float(row.sugar or 0),
            'fiber': float(row.fiber or 0),
            'calcium': float(row.calcium or 0),
            'iron': float(row.iron or 0),
            'phosphorus': float(row.phosphorus or 0),
            'potassium': float(row.potassium or 0),
            'sodium': float(row.sodium or 0),
            'vitamin_a': float(row.vitamin_a or 0),
            'vitamin_c': float(row.vitamin_c or 0),
        }

    def _score_foods_match(self, query, row):
        """로컬 DB 후보의 적합도 점수 (낮을수록 좋음)"""
        name = row.food_name or ''
        score = 0

        if name == query:
            return -1000
        if name.startswith(query):
            score -= 500

        parts = re.split(r'[_\s/&]', name)
        for part in parts:
            if part == query:
                score -= 300
                break

        score += len(name) * 2

        origin = row.origin or ''
        if '가정식' in origin:
            score -= 100
        elif '급식' in origin or '어린이' in origin:
            score -= 80

        if '세트' in name or '식단' in name or '&' in name:
            score += 500

        # 짧은 쿼리(원재료명)에서 접두사만 일치하고 구분자 없이 이어지면 페널티
        if name.startswith(query) and len(query) <= 3:
            remainder = name[len(query):]
            if remainder and not re.match(r'^[_\s/]', remainder):
                score += len(remainder) * 50

        # 가공식품 카테고리 페널티 (빙과류, 과자류, 잼류 → 원재료와 다른 식품)
        category = row.category or ''
        if any(cat in category for cat in ['빙과', '잼', '특수의료']):
            score += 300

        return score

    def _load_disk_cache(self):
        """디스크 캐시 파일에서 인메모리 캐시 복원"""
        try:
            if os.path.exists(self._disk_cache_path):
                with open(self._disk_cache_path, 'r', encoding='utf-8') as f:
                    disk_data = json.load(f)
                now = time.time()
                for key, entry in disk_data.items():
                    if now - entry.get('time', 0) < self._cache_ttl:
                        self._cache[key] = entry
        except Exception:
            pass

    def _save_disk_cache(self):
        """인메모리 캐시를 디스크에 저장"""
        try:
            cache_dir = os.path.dirname(self._disk_cache_path)
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir, exist_ok=True)
            now = time.time()
            valid = {k: v for k, v in self._cache.items() if now - v.get('time', 0) < self._cache_ttl}
            with open(self._disk_cache_path, 'w', encoding='utf-8') as f:
                json.dump(valid, f, ensure_ascii=False)
        except Exception:
            pass

    def _clean_menu_name(self, name):
        """메뉴명에서 알레르기 표기·특수문자 제거"""
        cleaned = CLEAN_PATTERN.sub('', name)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        cleaned = re.sub(r'\{\{green:(.*?)\}\}', r'\1', cleaned)
        return cleaned

    def _api_call(self, food_name, num_rows=10, api_base=None):
        """식약처 API 호출 (단일 메뉴명)"""
        if api_base is None:
            api_base = API_BASE
        params = {
            'serviceKey': API_KEY,
            'type': 'json',
            'pageNo': '1',
            'numOfRows': str(num_rows),
            'FOOD_NM_KR': food_name
        }
        url = api_base + '?' + urllib.parse.urlencode(params)
        try:
            req = urllib.request.Request(url)
            resp = urllib.request.urlopen(req, timeout=10)
            data = json.loads(resp.read().decode())
            return data.get('body', {}).get('items', [])
        except Exception:
            return []

    def _parse_nutrient(self, item):
        """API 응답 아이템에서 영양소 딕셔너리 추출"""
        result = {
            'name': item.get('FOOD_NM_KR', ''),
            'serving_size': item.get('SERVING_SIZE', '100g'),
            'category': item.get('FOOD_CAT1_NM', ''),
        }
        for key, (field, unit) in NUTRIENT_FIELDS.items():
            val = item.get(field, '')
            try:
                result[key] = float(val) if val and val.strip() else 0.0
            except (ValueError, TypeError):
                result[key] = 0.0
        return result

    def _score_match(self, query, item):
        """검색 결과 항목의 적합도 점수 계산 (낮을수록 좋음)"""
        name = item.get('FOOD_NM_KR', '')
        score = 0

        if name == query:
            return -1000

        if name.startswith(query):
            score -= 500

        parts = re.split(r'[_\s/&]', name)
        for part in parts:
            if part == query:
                score -= 300
                break

        score += len(name) * 2

        origin = item.get('FOOD_OR_NM', '')
        if '가정식' in origin:
            score -= 100
        elif '급식' in origin or '어린이' in origin:
            score -= 80

        if '세트' in name or '식단' in name or '&' in name:
            score += 500

        return score

    def _find_best_match(self, query, items):
        """검색 결과 중 가장 적합한 항목 선택"""
        if not items:
            return None

        scored = [(self._score_match(query, item), item) for item in items]
        scored.sort(key=lambda x: x[0])
        best_score, best_item = scored[0]

        name = best_item.get('FOOD_NM_KR', '')
        if len(name) > len(query) * 3 and best_score > 0:
            return None

        return best_item

    def _extract_base_ingredient(self, menu_name):
        """메뉴명에서 조리법 키워드를 제거하고 원재료명을 추출"""
        suffixes = ['나물무침', '나물', '무침', '볶음밥', '볶음', '조림', '구이', '찜', '튀김', '전', '탕', '국', '죽', '밥', '샐러드', '절임', '장아찌', '채', '생채', '겉절이', '비빔']
        result = menu_name
        for suffix in suffixes:
            if result.endswith(suffix) and len(result) > len(suffix) + 1:
                result = result[:-len(suffix)]
                break
        return result

    def _ai_select_best(self, query, candidates):
        """AI(Gemini)로 식약처 API 후보 중 최적 항목 선택"""
        if not candidates or len(candidates) <= 1:
            return candidates[0] if candidates else None
        try:
            gemini = wiz.model("gemini")
            candidate_list = [{'idx': i, 'name': c.get('FOOD_NM_KR', ''), 'category': c.get('FOOD_CAT1_NM', ''), 'origin': c.get('FOOD_OR_NM', '')} for i, c in enumerate(candidates[:10])]
            prompt = f"""어린이집 식단에 "{query}"라는 메뉴가 있습니다.
식약처 DB에서 검색한 후보 목록입니다:
{json.dumps(candidate_list, ensure_ascii=False)}

이 중 "{query}" 메뉴의 영양 정보로 가장 적합한 항목의 idx 번호를 하나만 선택해주세요.
어린이 급식 기준으로, 가정식/급식 형태를 우선하고, 세트메뉴나 복합식품은 피해주세요.
반드시 JSON 형식으로만 응답: {{"idx": 0}}"""
            result = gemini.ask_json(prompt)
            if isinstance(result, dict) and 'idx' in result:
                idx = int(result['idx'])
                if 0 <= idx < len(candidates):
                    return candidates[idx]
        except Exception:
            pass
        return None

    def search(self, menu_name):
        """메뉴명으로 영양성분 검색 (캐시 포함)
        검색 순서: 인메모리 캐시 → DB 매핑 캐시 → 기본재료 → 국가표준식품성분 API → 메뉴젠 API → AI fallback"""
        cleaned = self._clean_menu_name(menu_name)
        if not cleaned:
            return None

        # 1단계: 인메모리 캐시 확인
        with self._lock:
            if cleaned in self._cache:
                entry = self._cache[cleaned]
                if time.time() - entry['time'] < self._cache_ttl:
                    return entry['data']

        # 2단계: DB 매핑 캐시 확인 (영구 저장)
        #   ai_estimate 캐시는 신뢰도가 낮으므로, 로컬 DB에 있으면 재검색하여 교체
        db_result = self._db_mapping_get(cleaned)
        if db_result is not None:
            if db_result.get('is_estimated') or db_result.get('source') == 'ai_estimate':
                # AI 추정 결과 → 로컬 DB에서 더 정확한 결과가 있는지 재검색
                db_food_result = self._db_search(cleaned)
                if db_food_result is not None:
                    food_name_matched = db_food_result.get('name', '')
                    self._db_mapping_save(cleaned, db_food_result, food_name=food_name_matched, source='local_db')
                    with self._lock:
                        self._cache[cleaned] = {'data': db_food_result, 'time': time.time()}
                    return db_food_result
            with self._lock:
                self._cache[cleaned] = {'data': db_result, 'time': time.time()}
            return db_result

        # 3단계: 기본 재료 사전 확인
        if cleaned in BASIC_INGREDIENTS:
            result = dict(BASIC_INGREDIENTS[cleaned])
            self._db_mapping_save(cleaned, result, source='basic')
            with self._lock:
                self._cache[cleaned] = {'data': result, 'time': time.time()}
            return result

        # 3.5단계: 로컬 nutrition_foods DB 검색 (API 호출 대체)
        db_food_result = self._db_search(cleaned)
        if db_food_result is not None:
            food_name_matched = db_food_result.get('name', '')
            self._db_mapping_save(cleaned, db_food_result, food_name=food_name_matched, source='local_db')
            with self._lock:
                self._cache[cleaned] = {'data': db_food_result, 'time': time.time()}
            return db_food_result

        # 4단계: 국가표준식품성분 API (원본 메뉴명) — 로컬 DB에서 못 찾은 경우 fallback
        items = self._api_call(cleaned)
        best = self._find_best_match(cleaned, items)
        search_source = 'api'

        # 4-1: 원본 검색 실패 시 원재료명으로 재검색
        if not best and len(cleaned) > 2:
            base = self._extract_base_ingredient(cleaned)
            if base != cleaned:
                items = self._api_call(base)
                best = self._find_best_match(base, items)

        # 4-2: 여전히 실패 시 기존 접미사 제거 방식
        if not best and len(cleaned) > 2:
            for suffix in ['나물', '무침', '볶음', '조림', '구이', '찜', '튀김', '전', '탕', '국', '죽', '밥']:
                if cleaned.endswith(suffix) and len(cleaned) > len(suffix) + 1:
                    base = cleaned[:-len(suffix)]
                    items = self._api_call(base)
                    best = self._find_best_match(base, items)
                    if best:
                        break

        # 5단계: 메뉴젠 API (복합조리식)
        if not best:
            items = self._api_call(cleaned, api_base=API_BASE_MENUGEN)
            best = self._find_best_match(cleaned, items)
            if best:
                search_source = 'menugen'

        # 5-1: 메뉴젠에서도 스코어 매칭 실패 시 AI로 최적 후보 선택
        if not best:
            # 모든 API 소스에서 후보 수집
            all_candidates = self._api_call(cleaned, num_rows=20)
            all_candidates += self._api_call(cleaned, num_rows=20, api_base=API_BASE_MENUGEN)
            if all_candidates:
                best = self._ai_select_best(cleaned, all_candidates)
                if best:
                    search_source = 'ai_matched'

        result = self._parse_nutrient(best) if best else None
        food_code = best.get('FOOD_CD', '') if best else None
        food_name = best.get('FOOD_NM_KR', '') if best else None

        # 6단계: AI fallback (모든 API 실패 시)
        if result is None:
            result = self._ai_fallback(cleaned)
            search_source = 'ai_estimate'

        # DB 매핑에 결과 저장 (영구 캐시)
        if result is not None:
            self._db_mapping_save(cleaned, result, food_code=food_code, food_name=food_name, source=search_source)

        with self._lock:
            self._cache[cleaned] = {'data': result, 'time': time.time()}
            if len(self._cache) % 10 == 0:
                self._save_disk_cache()

        return result

    def _ai_fallback(self, food_name):
        """AI(Gemini)를 통한 영양소 추정 fallback — per 100g 기준으로 요청"""
        try:
            gemini = wiz.model("gemini")
            category_list = "밥류, 국 및 탕류, 나물·숙채류, 볶음류, 구이류, 찜류, 조림류, 튀김류, 과일류, 유제품, 빵 및 과자류, 김치류, 면 및 만두류"
            prompt = f"""한국 어린이집 급식 기준, '{food_name}'의 **100g당** 영양 성분을 추정해주세요.
category는 다음 중 가장 적합한 것을 선택: [{category_list}]
반드시 아래 JSON 형식으로만 응답하세요. 수치는 숫자만, 0보다 큰 현실적인 값으로.
{{"name": "{food_name}", "serving_size": "100g", "category": "국 및 탕류", "calories": 0, "protein": 0, "fat": 0, "carbohydrate": 0, "sugar": 0, "fiber": 0, "calcium": 0, "iron": 0, "phosphorus": 0, "potassium": 0, "sodium": 0, "vitamin_a": 0, "vitamin_c": 0}}"""
            result = gemini.ask_json(prompt)
            if isinstance(result, dict) and result.get('calories', 0) > 0:
                result['source'] = 'ai_estimate'
                result['is_estimated'] = True
                return result
        except Exception:
            pass
        return None

    def _ai_fallback_batch(self, food_names):
        """여러 음식의 영양성분을 Gemini로 일괄 추정 (is_estimated=True).
        반환: {food_name: nutrient_dict, ...}"""
        if not food_names:
            return {}
        results = {}
        try:
            gemini = wiz.model("gemini")
            category_list = "밥류, 국 및 탕류, 나물·숙채류, 볶음류, 구이류, 찜류, 조림류, 튀김류, 과일류, 유제품, 빵 및 과자류, 김치류, 면 및 만두류"
            food_list_str = json.dumps(food_names, ensure_ascii=False)
            prompt = f"""한국 어린이집 급식 기준, 아래 음식 각각의 **100g당** 영양 성분을 추정해주세요.
category는 다음 중 선택: [{category_list}]
수치는 0보다 큰 현실적인 값으로 추정하세요. 절대 0이나 null을 넣지 마세요.

음식 목록: {food_list_str}

반드시 아래 JSON 배열 형식으로만 응답, 다른 텍스트 없이:
[{{"name": "음식명", "serving_size": "100g", "category": "카테고리", "calories": 숫자, "protein": 숫자, "fat": 숫자, "carbohydrate": 숫자, "sugar": 숫자, "fiber": 숫자, "calcium": 숫자, "iron": 숫자, "phosphorus": 숫자, "potassium": 숫자, "sodium": 숫자, "vitamin_a": 숫자, "vitamin_c": 숫자}}]"""
            ai_result = gemini.ask_json(prompt)
            if isinstance(ai_result, list):
                for item in ai_result:
                    if isinstance(item, dict) and item.get('calories', 0) > 0:
                        name = item.get('name', '')
                        item['source'] = 'ai_estimate'
                        item['is_estimated'] = True
                        results[name] = item
        except Exception:
            pass
        # 개별 fallback: 일괄 추정에서 누락된 항목
        for name in food_names:
            if name not in results:
                single = self._ai_fallback(name)
                if single:
                    results[name] = single
        return results

    def normalize_food_names(self, food_list):
        """음식명 리스트 전체를 Gemini로 식약처 검색용 이름으로 일괄 정규화.
        반환: [{"original": "...", "search": "..."}, {"original": "...", "search_list": ["...", ...]}, ...]"""
        if not food_list:
            return []
        try:
            gemini = wiz.model("gemini")
            food_list_str = json.dumps(food_list, ensure_ascii=False)
            prompt = f"""다음은 어린이집 급식표의 음식 이름 목록입니다.
각각을 한국 식약처 식품영양성분 DB에서 검색하기 가장 적합한 이름으로 변환해주세요.

규칙:
- 복합 음식은 대표 재료 하나만 (두부피망볶음 → 두부볶음)
- 붙어있는 두 음식은 분리 (한과매실차 → 한과 / 매실차)
- 조리법보다 재료명 위주로
- 이미 검색에 적합한 단순 음식명(우유, 쌀밥, 배추김치 등)은 그대로 유지
- 반드시 아래 JSON 형식으로만 반환, 다른 텍스트 없이

입력: {food_list_str}

반환 형식:
[
  {{"original": "두부피망볶음", "search": "두부볶음"}},
  {{"original": "한과매실차", "search_list": ["한과", "매실차"]}},
  {{"original": "쌀밥", "search": "쌀밥"}}
]"""
            result = gemini.ask_json(prompt)
            if isinstance(result, list):
                # 원본 이름이 누락된 항목 보완
                originals_in_result = set()
                for item in result:
                    if isinstance(item, dict):
                        originals_in_result.add(item.get('original', ''))
                for name in food_list:
                    if name not in originals_in_result:
                        result.append({"original": name, "search": name})
                return result
        except Exception:
            pass
        # Gemini 실패 시 원본 그대로 반환
        return [{"original": name, "search": name} for name in food_list]

    def search_batch(self, normalized_items):
        """정규화된 음식명 목록으로 병렬 검색.
        Args: normalized_items — normalize_food_names() 반환값
        Returns: {original_name: {"result": nutrient_dict or None, "search_names": [...]}, ...}"""
        if not normalized_items:
            return {}
        # 검색할 고유 이름 수집
        search_names = set()
        for item in normalized_items:
            if not isinstance(item, dict):
                continue
            if 'search_list' in item:
                for s in item['search_list']:
                    search_names.add(s)
            elif 'search' in item:
                search_names.add(item['search'])
        search_names = list(search_names)
        # 병렬 검색 (기존 search() 파이프라인 재활용)
        search_results = {}
        if search_names:
            with ThreadPoolExecutor(max_workers=min(len(search_names), 8)) as executor:
                futures = {executor.submit(self.search, name): name for name in search_names}
                for future in as_completed(futures):
                    name = futures[future]
                    try:
                        search_results[name] = future.result()
                    except Exception:
                        search_results[name] = None
        # 결과를 original 기준으로 매핑
        batch_results = {}
        for item in normalized_items:
            if not isinstance(item, dict):
                continue
            original = item.get('original', '')
            if 'search_list' in item:
                # 분리된 음식: 각각의 결과를 리스트로
                sub_results = []
                for s in item['search_list']:
                    sub_results.append({
                        'search_name': s,
                        'result': search_results.get(s)
                    })
                batch_results[original] = {
                    'result': sub_results,
                    'search_names': item['search_list'],
                    'is_split': True
                }
            else:
                search_name = item.get('search', original)
                batch_results[original] = {
                    'result': search_results.get(search_name),
                    'search_names': [search_name],
                    'is_split': False
                }
        return batch_results

    def analyze_meal_pipeline(self, meal_content, age_group='1~2세'):
        """통합 파이프라인: [1] Gemini 일괄 정규화 → [2] 병렬 식약처 검색 → [3] Gemini fallback 보완.
        search_meal()과 동일한 반환 형식을 유지하여 호환성 보장."""
        if not meal_content:
            return {'menus': [], 'total': {}, 'found_count': 0, 'total_count': 0}

        # === 메뉴 파싱 (search_meal의 파싱 로직 재활용) ===
        content = meal_content
        for young_menu, old_menu in AGE_MENU_PAIRS:
            young_pat = r'\s*'.join(re.escape(ch) for ch in young_menu)
            old_pat = r'\s*'.join(re.escape(ch) for ch in old_menu)
            pattern = young_pat + r'\s*' + old_pat
            replacement = young_menu if age_group == '1~2세' else old_menu
            content = re.sub(pattern, replacement, content)

        lines = [l.strip() for l in content.replace('\r\n', '\n').split('\n') if l.strip()]
        menu_entries = []
        prev_item_idx = None

        for line in lines:
            green_matches = GREEN_PATTERN.findall(line)
            line_cleaned = GREEN_PATTERN.sub('', line).strip()

            if green_matches:
                green_items = []
                for raw in green_matches:
                    gname = self._clean_menu_name(raw.replace('{{green:', '').replace('}}', ''))
                    if gname and gname not in ('/', '-'):
                        green_items.append(gname)
                if green_items:
                    if age_group == '1~2세':
                        for gname in green_items:
                            menu_entries.append((gname, False))
                        if prev_item_idx is not None:
                            old_name, _ = menu_entries[prev_item_idx]
                            menu_entries[prev_item_idx] = (old_name, True)
                    else:
                        for gname in green_items:
                            menu_entries.append((gname, True))
                if line_cleaned:
                    cleaned = self._clean_menu_name(line_cleaned)
                    if cleaned and cleaned not in ('/', '-'):
                        prev_item_idx = len(menu_entries)
                        menu_entries.append((cleaned, False))
                    else:
                        prev_item_idx = None
                else:
                    prev_item_idx = None
            else:
                if line_cleaned:
                    cleaned = self._clean_menu_name(line_cleaned)
                    if cleaned and cleaned not in ('/', '-'):
                        prev_item_idx = len(menu_entries)
                        menu_entries.append((cleaned, False))

        if not menu_entries:
            return {'menus': [], 'total': {}, 'found_count': 0, 'total_count': 0}

        # === [1] Gemini 일괄 정규화 ===
        unique_names = list(set(name for name, _ in menu_entries))
        normalized = self.normalize_food_names(unique_names)

        # === [2] 병렬 식약처 검색 ===
        batch_results = self.search_batch(normalized)

        # === [3] 못 찾은 항목 → Gemini 일괄 fallback ===
        missing_names = []
        for original, info in batch_results.items():
            if info.get('is_split'):
                for sub in info['result']:
                    if sub.get('result') is None:
                        missing_names.append(sub['search_name'])
            else:
                if info.get('result') is None:
                    missing_names.extend(info['search_names'])

        fallback_results = {}
        if missing_names:
            fallback_results = self._ai_fallback_batch(list(set(missing_names)))
            # fallback 결과를 DB 캐시에 저장
            for fname, fdata in fallback_results.items():
                self._db_mapping_save(fname, fdata, source='ai_estimate')
                with self._lock:
                    self._cache[fname] = {'data': fdata, 'time': time.time()}

        # fallback 결과를 batch_results에 병합
        for original, info in batch_results.items():
            if info.get('is_split'):
                for sub in info['result']:
                    if sub.get('result') is None and sub['search_name'] in fallback_results:
                        sub['result'] = fallback_results[sub['search_name']]
            else:
                if info.get('result') is None:
                    for sname in info['search_names']:
                        if sname in fallback_results:
                            info['result'] = fallback_results[sname]
                            break

        # === [3.5] AI 매칭 검증 — 원래 음식과 API 매칭 결과가 맞는지 확인 ===
        verify_items = []
        for original, info in batch_results.items():
            if info.get('is_split'):
                continue
            result = info.get('result')
            if result and not result.get('is_estimated'):
                matched = result.get('name', '')
                category = result.get('category', '')
                if matched and matched != original:
                    verify_items.append({
                        'original': original,
                        'matched': matched,
                        'category': category,
                        'calories': result.get('calories', 0),
                    })

        if verify_items:
            mismatch_names = self._verify_food_matches(verify_items)
            if mismatch_names:
                print(f"[매칭검증] 불일치 감지: {mismatch_names}")
                # 불일치 항목은 AI fallback으로 교체
                re_fallback = self._ai_fallback_batch(mismatch_names)
                for fname, fdata in re_fallback.items():
                    self._db_mapping_save(fname, fdata, source='ai_estimate')
                    with self._lock:
                        self._cache[fname] = {'data': fdata, 'time': time.time()}
                for original, info in batch_results.items():
                    if original in mismatch_names and original in re_fallback:
                        info['result'] = re_fallback[original]
                        print(f"  [교체] {original}: API→AI추정 ({re_fallback[original].get('calories',0)}kcal/100g)")

        # === 결과 조립 (search_meal 호환 형식) ===
        menus = []
        total = {k: 0.0 for k in NUTRIENT_FIELDS}
        found_count = 0

        for cleaned, is_substitute in menu_entries:
            info = batch_results.get(cleaned, {})
            scaled_nutrition = None
            is_estimated = False

            if info.get('is_split'):
                # 분리된 음식: 각 서브 결과의 영양소를 합산
                combined = {k: 0.0 for k in NUTRIENT_FIELDS}
                any_found = False
                any_estimated = False
                for sub in info.get('result', []):
                    r = sub.get('result')
                    if r:
                        any_found = True
                        if r.get('is_estimated'):
                            any_estimated = True
                        ratio = self._get_serving_ratio(r, age_group)
                        for k in NUTRIENT_FIELDS:
                            if k in r and isinstance(r[k], (int, float)):
                                combined[k] += r[k] * ratio
                if any_found:
                    for k in combined:
                        combined[k] = round(combined[k], 2)
                    combined['name'] = cleaned
                    combined['serving_size'] = '1인분'
                    combined['category'] = ''
                    if any_estimated:
                        combined['is_estimated'] = True
                    scaled_nutrition = combined
                is_estimated = any_estimated
            else:
                result = info.get('result')
                if result:
                    is_estimated = bool(result.get('is_estimated'))
                    serving_ratio = self._get_serving_ratio(result, age_group)
                    if serving_ratio != 1.0:
                        scaled_nutrition = {}
                        for k, v in result.items():
                            if k in NUTRIENT_FIELDS and isinstance(v, (int, float)):
                                scaled_nutrition[k] = round(v * serving_ratio, 2)
                            else:
                                scaled_nutrition[k] = v
                        scaled_nutrition['serving_ratio'] = serving_ratio
                    else:
                        scaled_nutrition = result

            entry = {
                'name': cleaned,
                'found': scaled_nutrition is not None,
                'nutrition': scaled_nutrition,
                'is_substitute': is_substitute,
                'is_estimated': is_estimated
            }
            menus.append(entry)

            if scaled_nutrition:
                found_count += 1
                for key in NUTRIENT_FIELDS:
                    total[key] += scaled_nutrition.get(key, 0.0)

        for key in total:
            total[key] = round(total[key], 1)

        return {
            'menus': menus,
            'total': total,
            'found_count': found_count,
            'total_count': len(menus)
        }

    def _verify_food_matches(self, verify_items):
        """API 매칭 결과가 원래 음식과 일치하는지 AI로 검증.
        Args: verify_items — [{'original': '찐고구마', 'matched': '고구마전', 'category': '전·적 및 부침류', 'calories': 103}, ...]
        Returns: 불일치하는 원본 음식명 리스트"""
        if not verify_items:
            return []
        try:
            gemini = wiz.model("gemini")
            items_str = json.dumps(verify_items, ensure_ascii=False)
            prompt = f"""어린이집 급식표의 음식 이름(original)과 식약처 API에서 매칭된 결과(matched, category)를 비교합니다.

각 항목에서 원래 음식과 매칭된 식품이 **같은 음식 또는 같은 조리법**인지 판단하세요.
- 조리법이 다르면 불일치 (예: "찐고구마"는 쪄서 만든 것인데 "고구마전"은 부침 → 불일치)
- 재료는 같지만 조리법이 완전히 다르면 불일치
- 단순 표기 차이(쌀밥↔흰쌀밥)나 약간의 차이(가자미조림↔가자미조림)는 일치로 판단

입력: {items_str}

불일치하는 항목의 original 이름만 JSON 배열로 반환하세요.
모두 일치하면 빈 배열 [] 을 반환하세요.
예: ["찐고구마", "콩나물국"]"""
            result = gemini.ask_json(prompt)
            if isinstance(result, list):
                return [name for name in result if isinstance(name, str)]
        except Exception as e:
            print(f"[매칭검증] AI 검증 실패: {e}")
        return []

    def _get_serving_ratio(self, result, age_group='1~2세'):
        """per-100g/100mL 데이터를 어린이 1인분 제공량(g)으로 스케일링하는 비율 반환.
        이미 1인분 기준인 데이터(AI 추정 등)는 1.0 반환."""
        if not result:
            return 1.0
        serving = str(result.get('serving_size', '100g')).strip().lower()
        # 이미 1인분 단위인 경우 스케일링 불필요
        if '1인분' in serving or '인분' in serving:
            return 1.0
        # per-100g/100mL인 경우 카테고리별 어린이 제공량으로 변환
        if '100' in serving:
            category = result.get('category', '기타')
            weights = SERVING_WEIGHTS.get(age_group, SERVING_WEIGHTS.get('1~2세', {}))
            # 카테고리 매핑
            cat_map = {
                '밥류': '밥류', '곡류': '밥류',
                '국 및 탕류': '국 및 탕류', '찌개 및 전골류': '국 및 탕류',
                '나물·숙채류': '나물·숙채류', '채소류': '나물·숙채류',
                '볶음류': '볶음류',
                '구이류': '구이류',
                '찜류': '찜류',
                '조림류': '조림류',
                '튀김류': '튀김류',
                '과일류': '과일류',
                '유제품': '유제품',
                '빵 및 과자류': '빵 및 과자류',
                '김치류': '나물·숙채류',
                '면 및 만두류': '밥류',
                '즉석식품류': '볶음류',
            }
            mapped = cat_map.get(category, '기타')
            serving_g = weights.get(mapped, weights.get('기타', 50))
            return serving_g / 100.0
        return 1.0

    def search_meal(self, meal_content, age_group='1~2세'):
        """식단 내용(여러 메뉴)에서 각 메뉴의 영양소를 병렬 조회하고 합산.
        연령에 따라 green 마커와 연결 메뉴를 분기 처리한다.
        - 1~2세: green 아이템이 실제 메뉴, 직전 원본은 대체식(3~5세용)
        - 3~5세: green 아이템이 대체식(1~2세용), 원본이 실제 메뉴
        - 백김치배추김치 등 연결 표기: 연령에 맞는 것만 선택
        per-100g 데이터는 어린이 1인분 제공량으로 자동 스케일링."""
        if not meal_content:
            return {'menus': [], 'total': {}, 'found_count': 0, 'total_count': 0}

        # 연령별 연결 메뉴 분리 (e.g., 백김치배추김치, 백김치배추 김치 → 연령에 맞는 것만)
        content = meal_content
        for young_menu, old_menu in AGE_MENU_PAIRS:
            # 메뉴명 사이의 공백을 허용하는 패턴 (e.g., '백김치배추 김치')
            young_pat = r'\s*'.join(re.escape(ch) for ch in young_menu)
            old_pat = r'\s*'.join(re.escape(ch) for ch in old_menu)
            pattern = young_pat + r'\s*' + old_pat
            replacement = young_menu if age_group == '1~2세' else old_menu
            content = re.sub(pattern, replacement, content)

        lines = [l.strip() for l in content.replace('\r\n', '\n').split('\n') if l.strip()]

        # 연령 인식 메뉴 추출
        # green 마커 = 1~2세 전용 메뉴, 직전 원본 = 3~5세 전용 메뉴
        menu_entries = []  # (cleaned_name, is_substitute)
        prev_item_idx = None  # 직전 비-green 아이템의 인덱스 (green 대체 대상)

        for line in lines:
            green_matches = GREEN_PATTERN.findall(line)
            line_cleaned = GREEN_PATTERN.sub('', line).strip()

            if green_matches:
                green_items = []
                for raw in green_matches:
                    gname = self._clean_menu_name(raw.replace('{{green:', '').replace('}}', ''))
                    if gname and gname not in ('/', '-'):
                        green_items.append(gname)

                if green_items:
                    if age_group == '1~2세':
                        # 1~2세: green 아이템이 실제 메뉴
                        for gname in green_items:
                            menu_entries.append((gname, False))
                        # 직전 원본(3~5세용)을 대체식으로 전환
                        if prev_item_idx is not None:
                            old_name, _ = menu_entries[prev_item_idx]
                            menu_entries[prev_item_idx] = (old_name, True)
                    else:
                        # 3~5세: green 아이템이 대체식
                        for gname in green_items:
                            menu_entries.append((gname, True))

                # 같은 줄의 비-green 텍스트 = 공통 메뉴
                if line_cleaned:
                    cleaned = self._clean_menu_name(line_cleaned)
                    if cleaned and cleaned not in ('/', '-'):
                        prev_item_idx = len(menu_entries)
                        menu_entries.append((cleaned, False))
                    else:
                        prev_item_idx = None
                else:
                    prev_item_idx = None
            else:
                # green 없는 일반 메뉴
                if line_cleaned:
                    cleaned = self._clean_menu_name(line_cleaned)
                    if cleaned and cleaned not in ('/', '-'):
                        prev_item_idx = len(menu_entries)
                        menu_entries.append((cleaned, False))

        if not menu_entries:
            return {'menus': [], 'total': {}, 'found_count': 0, 'total_count': 0}

        # 중복 제거된 이름 목록으로 병렬 검색
        unique_names = list(set(name for name, _ in menu_entries))

        results_map = {}
        with ThreadPoolExecutor(max_workers=min(len(unique_names), 8)) as executor:
            futures = {executor.submit(self.search, name): name for name in unique_names}
            for future in as_completed(futures):
                name = futures[future]
                try:
                    results_map[name] = future.result()
                except Exception:
                    results_map[name] = None

        menus = []
        total = {k: 0.0 for k in NUTRIENT_FIELDS}
        found_count = 0

        for cleaned, is_substitute in menu_entries:
            result = results_map.get(cleaned)
            # per-100g → 1인분 스케일링
            scaled_nutrition = None
            serving_ratio = 1.0
            if result:
                serving_ratio = self._get_serving_ratio(result, age_group)
                if serving_ratio != 1.0:
                    scaled_nutrition = {}
                    for k, v in result.items():
                        if k in NUTRIENT_FIELDS and isinstance(v, (int, float)):
                            scaled_nutrition[k] = round(v * serving_ratio, 2)
                        else:
                            scaled_nutrition[k] = v
                    scaled_nutrition['serving_ratio'] = serving_ratio
                else:
                    scaled_nutrition = result

            entry = {
                'name': cleaned,
                'found': result is not None,
                'nutrition': scaled_nutrition,
                'is_substitute': is_substitute,
                'is_estimated': bool(result.get('is_estimated')) if result else False
            }
            menus.append(entry)

            if scaled_nutrition:
                found_count += 1
                for key in NUTRIENT_FIELDS:
                    total[key] += scaled_nutrition.get(key, 0.0)

        for key in total:
            total[key] = round(total[key], 1)

        return {
            'menus': menus,
            'total': total,
            'found_count': found_count,
            'total_count': len(menus)
        }

    def scale_to_target(self, meal_result, target_kcal):
        """식약처 API 합산 영양소를 실제 HWP 파싱 열량(target_kcal)에 맞게 비율 보정.
        
        Args:
            meal_result: search_meal() 반환값
            target_kcal: DB에 저장된 HWP 파싱 실제 열량 (kcal)
        
        Returns:
            보정된 total dict (각 영양소가 비율 조정됨)
        """
        api_total_kcal = meal_result.get('total', {}).get('calories', 0)
        if not api_total_kcal or api_total_kcal <= 0 or not target_kcal or target_kcal <= 0:
            return dict(meal_result.get('total', {}))

        ratio = target_kcal / api_total_kcal
        scaled = {}
        for key, val in meal_result.get('total', {}).items():
            scaled[key] = round(val * ratio, 1)

        return scaled

    def get_meal_expected_kcal(self, meal_type, age_group='1~2세'):
        """끼니별 예상 칼로리 계산 (DB kcal 없을 때 스케일링 기준)"""
        daily = DAILY_ENERGY.get(age_group, 1000)
        ratio = MEAL_RATIOS.get(meal_type, MEAL_RATIOS.get('기타', 0.10))
        return round(daily * ratio)

    def compute_scaled_nutrients(self, meal_result, meal_type='점심', age_group='1~2세', db_kcal=None):
        """통합 영양소 스케일링 함수.
        - db_kcal이 있으면: 해당 값으로 스케일링
        - db_kcal이 없으면: 끼니별 예상 칼로리로 스케일링
        """
        if db_kcal and db_kcal > 0:
            return self.scale_to_target(meal_result, db_kcal)
        expected = self.get_meal_expected_kcal(meal_type, age_group)
        return self.scale_to_target(meal_result, expected)

    def clear_cache(self):
        """캐시 초기화"""
        with self._lock:
            self._cache.clear()
        try:
            if os.path.exists(self._disk_cache_path):
                os.remove(self._disk_cache_path)
        except Exception:
            pass

Model = NutritionAPI()
