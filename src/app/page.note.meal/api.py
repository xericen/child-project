# pyright: reportUndefinedVariable=false, reportMissingImports=false
import datetime
import os
import re
import subprocess
import glob
import io
import tempfile
import shutil
import json
from PIL import Image

MAX_IMAGE_WIDTH = 1200
JPEG_QUALITY = 85

KST = datetime.timezone(datetime.timedelta(hours=9))

def _now_kst():
    return datetime.datetime.now(KST)

# 표준 19종 알레르기 유발 식품 매핑 (번호 → 식품명)
ALLERGY_MAP = {
    1: '난류', 2: '우유', 3: '메밀', 4: '땅콩', 5: '대두',
    6: '밀', 7: '고등어', 8: '게', 9: '새우', 10: '돼지고기',
    11: '복숭아', 12: '토마토', 13: '아황산류', 14: '호두',
    15: '닭고기', 16: '소고기', 17: '오징어', 18: '조개류', 19: '잣'
}

# child_allergies 테이블의 allergy_type 값 → 표준 번호 매핑
ALLERGY_TYPE_TO_NUMBERS = {
    '계란': [1],
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
    '소고기': [16],
    '쇠고기': [16],
    '오징어': [17],
    '조개류': [18],
    '잣': [19],
    '난류': [1],
}

# 7가지 식단 테마 정의 (HWP 식단안내 기준)
MEAL_THEMES = {
    '이달의식재료': {'emoji': '🥬', 'keywords': ['이달의식재료', '제철식재료', '월별식재료', '제철']},
    '세계밥상': {'emoji': '🌍', 'keywords': ['세계밥상', '세계문화', '세계']},
    '상영양식': {'emoji': '🥗', 'keywords': ['상영양식', '저염식단', '국없는날', '나트륨저감']},
    '차차밥상': {'emoji': '🍵', 'keywords': ['차차밥상', '저당식단', '차마시는날', '당류저감']},
    '新메뉴': {'emoji': '⭐', 'keywords': ['新메뉴', '신메뉴', '레시피콘테스트']},
    '신선식품': {'emoji': '🍎', 'keywords': ['신선식품', '신선한과일', '채소스틱']},
    '대체식': {'emoji': '🔄', 'keywords': ['대체식', '대체메뉴']},
}

# HWP 이미지 파일명 → 테마 매핑 (hwp5html 변환 결과 기준)
THEME_IMAGE_MAP = {
    'BIN000B': '이달의식재료',
    'BIN000C': '세계밥상',
    'BIN000D': '상영양식',
    'BIN000E': '차차밥상',
    'BIN000F': '新메뉴',
    'BIN0010': '신선식품',
    'BIN0011': '신선식품',
    'BIN0012': '신선식품',
    'BIN0013': '대체식',
}

def _extract_theme(text):
    """텍스트에서 식단 테마 키워드를 추출"""
    for theme_name, info in MEAL_THEMES.items():
        for kw in info['keywords']:
            if kw in text:
                return theme_name
    return None

def _compress_image(file_data, max_width=MAX_IMAGE_WIDTH, quality=JPEG_QUALITY):
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

Meals = wiz.model("db/childcheck/meals")
Notifications = wiz.model("db/childcheck/notifications")
Users = wiz.model("db/login_db/users")
push = wiz.model("push")
Children = wiz.model("db/childcheck/children")
ChildAllergies = wiz.model("db/childcheck/child_allergies")
AllergyCategories = wiz.model("db/childcheck/allergy_categories")
ServerMembers = wiz.model("db/login_db/server_members")

def _get_server_id():
    server_id = wiz.session.get("server_id") or wiz.session.get("join_server_id")
    if not server_id:
        wiz.response.status(401, message="서버 정보가 없습니다.")
    return int(server_id)

def _build_caution_food_map():
    """DB에서 주의식품→번호 역매핑을 생성 (예: '마가린' → [2])"""
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

def _get_child_allergy_numbers():
    """현재 로그인 학부모의 자녀 알레르기 번호 집합을 반환"""
    allergy_nums = set()
    try:
        user_id = int(wiz.session.get("id"))
        children_list = Children.select().where(Children.user_id == user_id)
        child_ids = [c.id for c in children_list]
        if child_ids:
            allergies = ChildAllergies.select().where(ChildAllergies.child_id.in_(child_ids))
            for allergy in allergies:
                atype = allergy.allergy_type
                if atype == '기타' and allergy.other_detail:
                    detail = allergy.other_detail.strip()
                    found = ALLERGY_TYPE_TO_NUMBERS.get(detail, [])
                    if found:
                        allergy_nums.update(found)
                    else:
                        for part in re.split(r'[,\s/]+', detail):
                            part = part.strip()
                            if part:
                                nums = ALLERGY_TYPE_TO_NUMBERS.get(part, [])
                                if nums:
                                    allergy_nums.update(nums)
                                else:
                                    # AI로 표준 19종 매핑 시도
                                    ai_nums = _ai_map_other_allergy(part)
                                    allergy_nums.update(ai_nums)
                elif atype in ALLERGY_TYPE_TO_NUMBERS:
                    allergy_nums.update(ALLERGY_TYPE_TO_NUMBERS[atype])
    except Exception:
        pass
    return allergy_nums

def notify_parents(server_id, noti_type, title, message, link=""):
    try:
        parent_ids = [sm.user_id for sm in ServerMembers.select(ServerMembers.user_id).where(
            (ServerMembers.server_id == server_id) & (ServerMembers.role == "parent")
        )]
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

def _extract_allergy_numbers(content):
    """원본 content에서 알레르기 번호 추출 (clean 전에 호출)"""
    numbers = set()

    # 분수 패턴(1/2, 1/3 등) 제거 — 서빙 사이즈이므로 알레르기 번호가 아님
    content = re.sub(r'\d+/\d+', '', content)

    # 원 숫자 ①~⑲ 추출
    circled_map = {
        '①': 1, '②': 2, '③': 3, '④': 4, '⑤': 5,
        '⑥': 6, '⑦': 7, '⑧': 8, '⑨': 9, '⑩': 10,
        '⑪': 11, '⑫': 12, '⑬': 13, '⑭': 14, '⑮': 15,
        '⑯': 16, '⑰': 17, '⑱': 18, '⑲': 19, '⑳': 20,
    }
    for char in content:
        if char in circled_map:
            num = circled_map[char]
            if 1 <= num <= 19:
                numbers.add(num)

    # 한글 뒤 숫자열: 미역국5.6 → [5, 6]
    for m in re.finditer(r'(?<=[가-힣])([0-9]+(?:[,.][ ]?[0-9]+)*)', content):
        for n in re.split(r'[,.\s]+', m.group(1)):
            if n.strip():
                try:
                    num = int(n.strip())
                    if 1 <= num <= 19:
                        numbers.add(num)
                except ValueError:
                    pass

    # 괄호 안 숫자: (1,2,3)
    for m in re.finditer(r'\(([0-9,.\s]+)\)', content):
        for n in re.split(r'[,.\s]+', m.group(1)):
            if n.strip():
                try:
                    num = int(n.strip())
                    if 1 <= num <= 19:
                        numbers.add(num)
                except ValueError:
                    pass

    return sorted(numbers)

def _extract_dish_allergies(raw_content):
    """원본 content에서 음식별 알레르기 번호를 추출하여 dict 반환"""
    circled_map = {
        '①': 1, '②': 2, '③': 3, '④': 4, '⑤': 5,
        '⑥': 6, '⑦': 7, '⑧': 8, '⑨': 9, '⑩': 10,
        '⑪': 11, '⑫': 12, '⑬': 13, '⑭': 14, '⑮': 15,
        '⑯': 16, '⑰': 17, '⑱': 18, '⑲': 19, '⑳': 20,
    }
    result = {}
    lines = raw_content.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # 분수 패턴(1/2, 1/3 등) 제거 — 서빙 사이즈
        line_clean = re.sub(r'\d+/\d+', '', line)
        # 라인에서 알레르기 번호 추출
        nums = set()
        for char in line_clean:
            if char in circled_map:
                num = circled_map[char]
                if 1 <= num <= 19:
                    nums.add(num)
        # 한글 뒤 숫자열: 미역국5.6
        for m in re.finditer(r'(?<=[가-힣])([0-9]+(?:[,.][ ]?[0-9]+)*)', line_clean):
            for n in re.split(r'[,.\s]+', m.group(1)):
                if n.strip():
                    try:
                        num = int(n.strip())
                        if 1 <= num <= 19:
                            nums.add(num)
                    except ValueError:
                        pass
        # 괄호 안 숫자: (1,2,3)
        for m in re.finditer(r'\(([0-9,.\s]+)\)', line_clean):
            for n in re.split(r'[,.\s]+', m.group(1)):
                if n.strip():
                    try:
                        num = int(n.strip())
                        if 1 <= num <= 19:
                            nums.add(num)
                    except ValueError:
                        pass
        # 음식명 정리 (번호 제거, 분수 패턴도 제거)
        dish = re.sub(r'\d+/\d+', '', line)
        dish = re.sub(r'[\u2460-\u2473\u3251-\u325F\u32B1-\u32BF\u24EA-\u24FF]', '', dish)
        dish = re.sub(r'\([0-9,.\s]+\)', '', dish)
        dish = re.sub(r'\[[0-9,.\s]+\]', '', dish)
        dish = re.sub(r'(?<=[가-힣])[0-9,.]+', '', dish)
        dish = re.sub(r'[\[\]/]', '', dish).strip()
        if dish and nums:
            result[dish] = sorted(nums)
    return result

def _clean_meal_content(content):
    """음식명에서 알레르기 번호, 특수문자 등 제거 ({{green:...}} 마커는 보존)"""
    # green 마커를 임시 플레이스홀더로 보호
    green_parts = []
    def _protect_green(m):
        idx = len(green_parts)
        inner = m.group(1)
        # 마커 내부도 알레르기 번호 등 정리
        inner = re.sub(r'[\u2460-\u2473\u3251-\u325F\u32B1-\u32BF\u24EA-\u24FF]', '', inner)
        inner = re.sub(r'\([0-9,.\s]+\)', '', inner)
        inner = re.sub(r'(?<=[가-힣])[0-9,.]+', '', inner)
        inner = re.sub(r'[\[\]]', '', inner)
        inner = inner.strip()
        green_parts.append(inner)
        return f'\x00GREEN{idx}\x00'
    content = re.sub(r'\{\{green:(.*?)\}\}', _protect_green, content)
    # 분수 패턴(1/2, 1/3 등) 제거 — 서빙 사이즈
    content = re.sub(r'\d+/\d+', '', content)
    # 원 숫자 (①②③...⑳ 등) 제거
    content = re.sub(r'[\u2460-\u2473\u3251-\u325F\u32B1-\u32BF\u24EA-\u24FF]', '', content)
    # 괄호 안 숫자 조합 제거: (1,2,3) (5.6)
    content = re.sub(r'\([0-9,.\s]+\)', '', content)
    # 대괄호 안 숫자 조합 제거: [1,2]
    content = re.sub(r'\[[0-9,.\s]+\]', '', content)
    # 한글 뒤 바로 붙은 숫자열 제거 (알레르기 표시): 미역국56 → 미역국
    content = re.sub(r'(?<=[가-힣])[0-9,.]+', '', content)
    # 단독 대괄호, 슬래시 문자 제거
    content = re.sub(r'[\[\]/]', '', content)
    # 여러 공백을 하나로
    content = re.sub(r'[ \t]+', ' ', content)
    # green 마커 복원
    def _restore_green(m):
        idx = int(m.group(1))
        if idx < len(green_parts) and green_parts[idx]:
            return '{{green:' + green_parts[idx] + '}}'
        return ''
    content = re.sub(r'\x00GREEN(\d+)\x00', _restore_green, content)
    # 줄별 정리
    lines = content.split('\n')
    cleaned = [line.strip() for line in lines if line.strip()]
    return '\n'.join(cleaned)

def _ai_analyze_dish_allergies(dish_allergy_map, content):
    """AI로 각 음식에 포함된 알레르기 원재료를 분석하여 dish_allergy_map 보강.
    HWP에 알레르기 번호가 표기되지 않은 음식도 AI가 원재료를 파악하여 번호를 추가한다."""
    # content에서 음식명 목록 추출
    lines = content.replace('\r\n', '\n').split('\n')
    dish_names = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # green 마커 내부 텍스트도 음식으로 취급
        greens = re.findall(r'\{\{green:(.*?)\}\}', line)
        for g in greens:
            gname = re.sub(r'[\u2460-\u2473\u3251-\u325F\d,.()（）\[\]]', '', g).strip()
            if gname:
                dish_names.append(gname)
        # green 마커 제거 후 나머지
        cleaned = re.sub(r'\{\{green:.*?\}\}', '', line).strip()
        cleaned = re.sub(r'[\u2460-\u2473\u3251-\u325F]', '', cleaned)
        cleaned = re.sub(r'\([0-9,.\s]+\)', '', cleaned)
        cleaned = re.sub(r'(?<=[가-힣])[0-9,.]+', '', cleaned)
        cleaned = re.sub(r'[\[\]/]', '', cleaned).strip()
        if cleaned:
            dish_names.append(cleaned)

    if not dish_names:
        return dish_allergy_map

    # 이미 번호가 있는 음식은 분석 불필요
    dishes_without_numbers = [d for d in dish_names if d not in dish_allergy_map or not dish_allergy_map[d]]

    if not dishes_without_numbers:
        return dish_allergy_map

    allergy_list = ", ".join([f"{v}({k}번)" for k, v in ALLERGY_MAP.items()])

    try:
        gemini = wiz.model("gemini")
        prompt = f"""어린이집 식단의 각 음식에 포함된 알레르기 유발 원재료를 분석해주세요.

표준 19종 알레르기: {allergy_list}

분석할 음식 목록:
{json.dumps(dishes_without_numbers, ensure_ascii=False)}

각 음식의 주재료를 파악하고, 표준 19종 중 해당하는 알레르기 번호를 매핑해주세요.
예시: 만둣국은 돼지고기(10번), 밀(6번) 포함. 계란후라이는 난류(1번) 포함.
확실한 것만 매핑하고, 불확실한 것은 제외하세요.

JSON 형식으로만 응답: {{"음식명": [번호1, 번호2], "음식명2": []}}"""

        result = gemini.ask_json(prompt, system_instruction="어린이 영양사입니다. 음식 재료 기반으로 알레르기 원재료를 정확히 분석합니다. JSON만 응답하세요.")
        if isinstance(result, dict):
            for dish_name, nums in result.items():
                if not isinstance(nums, list):
                    continue
                valid_nums = [int(n) for n in nums if isinstance(n, (int, float)) and 1 <= int(n) <= 19]
                if valid_nums:
                    # 기존 번호와 병합
                    existing = set(dish_allergy_map.get(dish_name, []))
                    existing.update(valid_nums)
                    dish_allergy_map[dish_name] = sorted(existing)
    except Exception:
        pass

    return dish_allergy_map

def _ai_map_other_allergy(other_detail):
    """기타 알레르기 키워드가 표준 19종 중 어디에 해당하는지 AI로 분석.
    ALLERGY_TYPE_TO_NUMBERS에 없는 키워드일 때 사용."""
    if not other_detail or not other_detail.strip():
        return []
    allergy_list = ", ".join([f"{v}({k}번)" for k, v in ALLERGY_MAP.items()])
    try:
        gemini = wiz.model("gemini")
        prompt = f"""아이의 알레르기가 "{other_detail}"입니다.

표준 19종 알레르기: {allergy_list}

이 알레르기가 표준 19종 중 어떤 항목에 해당하는지 번호만 반환해주세요.
예: "햄" → 돼지고기(10번), "카스테라" → 난류(1번), 밀(6번)
해당하는 게 없으면 빈 배열을 반환하세요.

JSON 형식: {{"numbers": [10]}}"""

        result = gemini.ask_json(prompt, system_instruction="알레르기 전문가입니다. JSON만 응답하세요.")
        if isinstance(result, dict) and 'numbers' in result:
            return [int(n) for n in result['numbers'] if isinstance(n, (int, float)) and 1 <= int(n) <= 19]
    except Exception:
        pass
    return []

def get_role():
    role = wiz.session.get("role")
    if not role:
        wiz.response.status(401, message="로그인이 필요합니다.")
    wiz.response.status(200, role=role)

def get_monthly():
    role = wiz.session.get("role")
    if not role:
        wiz.response.status(401, message="로그인이 필요합니다.")

    server_id = _get_server_id()
    month = wiz.request.query("month", "")
    if not month:
        month = datetime.date.today().strftime("%Y-%m")

    year, mon = month.split("-")
    year = int(year)
    mon = int(mon)

    start_date = datetime.date(year, mon, 1)
    if mon == 12:
        end_date = datetime.date(year + 1, 1, 1)
    else:
        end_date = datetime.date(year, mon + 1, 1)

    meals = {}
    try:
        rows = Meals.select().where(
            (Meals.server_id == server_id) & (Meals.meal_date >= start_date) & (Meals.meal_date < end_date)
        ).order_by(Meals.meal_date)
        for row in rows:
            date_str = row.meal_date.strftime("%Y-%m-%d") if hasattr(row.meal_date, 'strftime') else str(row.meal_date)
            if date_str not in meals:
                meals[date_str] = []
            meals[date_str].append({
                'id': row.id,
                'meal_type': row.meal_type,
                'content': row.content or '',
                'theme': row.theme or ''
            })
    except Exception:
        pass

    wiz.response.status(200, meals=meals)

def get_daily():
    role = wiz.session.get("role")
    if not role:
        wiz.response.status(401, message="로그인이 필요합니다.")

    server_id = _get_server_id()
    date_str = wiz.request.query("date", "")
    if not date_str:
        date_str = datetime.date.today().strftime("%Y-%m-%d")

    # 모든 역할에 대해 알레르기 번호 조회
    child_allergy_nums = set()
    if role == 'parent':
        child_allergy_nums = _get_child_allergy_numbers()
    elif role in ('teacher', 'director'):
        # 교사/원장: 서버 내 모든 자녀의 알레르기 번호를 합산
        try:
            parent_ids = [sm.user_id for sm in ServerMembers.select(ServerMembers.user_id).where(
                (ServerMembers.server_id == server_id) & (ServerMembers.role == "parent")
            )]
            if parent_ids:
                all_children = list(Children.select().where(Children.user_id.in_(parent_ids)))
                child_ids = [c.id for c in all_children]
                if child_ids:
                    for ca in ChildAllergies.select().where(ChildAllergies.child_id.in_(child_ids)):
                        if ca.allergy_type == '기타' and ca.other_detail:
                            detail = ca.other_detail.strip()
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
                        elif ca.allergy_type in ALLERGY_TYPE_TO_NUMBERS:
                            child_allergy_nums.update(ALLERGY_TYPE_TO_NUMBERS[ca.allergy_type])
        except Exception:
            pass

    meals = []
    try:
        rows = Meals.select().where(
            (Meals.server_id == server_id) & (Meals.meal_date == date_str)
        ).order_by(Meals.id)
        for row in rows:
            meal_data = {
                'id': row.id,
                'meal_type': row.meal_type,
                'content': row.content or '',
                'photo_path': row.photo_path or '',
                'theme': row.theme or '',
                'allergy_match': False,
                'matched_allergens': []
            }

            # 모든 역할: 알레르기 번호와 식단 알레르기 번호 교차 확인
            if child_allergy_nums:
                meal_nums = set()
                dish_allergy = {}
                try:
                    stored = row.allergy_numbers
                    if stored:
                        nums = json.loads(stored) if isinstance(stored, str) else stored
                        meal_nums = set(nums)
                except Exception:
                    pass
                try:
                    if row.dish_allergies:
                        dish_allergy = json.loads(row.dish_allergies)
                except Exception:
                    pass

                matched_allergens = set()
                matched_dishes = []

                # dish_allergies 기반 정밀 매칭
                if dish_allergy:
                    for dish_name, dish_nums in dish_allergy.items():
                        overlap = child_allergy_nums & set(dish_nums)
                        if overlap:
                            anames = [ALLERGY_MAP.get(n, str(n)) for n in sorted(overlap)]
                            matched_allergens.update(anames)
                            matched_dishes.append({'dish': dish_name, 'allergens': anames})

                # 전체 번호 교차 fallback
                if not matched_allergens:
                    overlap = child_allergy_nums & meal_nums
                    for n in overlap:
                        matched_allergens.add(ALLERGY_MAP.get(n, str(n)))

                if matched_allergens:
                    meal_data['allergy_match'] = True
                    meal_data['matched_allergens'] = sorted(matched_allergens)
                    meal_data['matched_dishes'] = matched_dishes

            meals.append(meal_data)
    except Exception:
        pass

    wiz.response.status(200, meals=meals)

def save_meal():
    role = wiz.session.get("role")
    if role not in ['teacher', 'director']:
        wiz.response.status(403, message="권한이 없습니다.")

    server_id = _get_server_id()
    user_id = wiz.session.get("id")
    meal_type = wiz.request.query("meal_type", True)
    meal_date = wiz.request.query("meal_date", True)
    content = wiz.request.query("content", True)
    kcal_str = wiz.request.query("kcal", "")
    kcal = int(kcal_str) if kcal_str else None
    protein_str = wiz.request.query("protein", "")
    protein = float(protein_str) if protein_str else None

    photo_path = ""
    files = wiz.request.files()
    if files and len(files) > 0:
        file = files[0]
        if file.filename:
            fs = wiz.project.fs("data", "meals")
            safe_name = meal_date + "_" + meal_type + "_" + str(_now_kst().timestamp()).replace(".", "") + ".jpg"
            save_path = fs.abspath(safe_name)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            compressed = _compress_image(file.read())
            with open(save_path, 'wb') as wf:
                wf.write(compressed)
            photo_path = f"/api/wiz/project/main/data/meals/{safe_name}"

    # 식단 내용에서 알레르기 번호 및 음식별 알레르기 매핑 추출
    allergy_nums = _extract_allergy_numbers(content)
    dish_allergy_map = _extract_dish_allergies(content)
    # AI로 번호 표기 없는 음식의 알레르기 원재료 분석
    dish_allergy_map = _ai_analyze_dish_allergies(dish_allergy_map, content)
    # AI 분석 결과의 번호도 allergy_nums에 병합
    for nums in dish_allergy_map.values():
        allergy_nums.update(nums) if isinstance(allergy_nums, set) else None
    allergy_nums_list = sorted(allergy_nums) if isinstance(allergy_nums, set) else allergy_nums

    try:
        Meals.create(
            server_id=server_id,
            meal_type=meal_type,
            meal_date=meal_date,
            content=content,
            kcal=kcal,
            protein=protein,
            photo_path=photo_path,
            allergy_numbers=json.dumps(allergy_nums_list),
            dish_allergies=json.dumps(dish_allergy_map, ensure_ascii=False),
            created_by=user_id
        )
    except Exception as e:
        wiz.response.status(500, message=str(e))

    type_labels = {"오전간식": "오전간식", "점심": "점심", "오후간식": "오후간식"}
    type_label = type_labels.get(meal_type, meal_type)
    notify_parents(server_id, "meal", f"{meal_date} {type_label} 식단 등록", content, "/note/meal")

    wiz.response.status(200)

def update_meal():
    role = wiz.session.get("role")
    if role not in ['teacher', 'director']:
        wiz.response.status(403, message="권한이 없습니다.")

    server_id = _get_server_id()
    meal_id = int(wiz.request.query("id", True))
    meal_type = wiz.request.query("meal_type", True)
    content = wiz.request.query("content", True)
    kcal_str = wiz.request.query("kcal", "")
    kcal = int(kcal_str) if kcal_str else None
    protein_str = wiz.request.query("protein", "")
    protein = float(protein_str) if protein_str else None

    # 식단 내용에서 알레르기 번호 및 음식별 알레르기 매핑 재추출
    allergy_nums = _extract_allergy_numbers(content)
    dish_allergy_map = _extract_dish_allergies(content)
    # AI로 번호 표기 없는 음식의 알레르기 원재료 분석
    dish_allergy_map = _ai_analyze_dish_allergies(dish_allergy_map, content)
    for nums in dish_allergy_map.values():
        allergy_nums.update(nums) if isinstance(allergy_nums, set) else None
    allergy_nums_list = sorted(allergy_nums) if isinstance(allergy_nums, set) else allergy_nums

    try:
        Meals.update(
            meal_type=meal_type,
            content=content,
            kcal=kcal,
            protein=protein,
            allergy_numbers=json.dumps(allergy_nums_list),
            dish_allergies=json.dumps(dish_allergy_map, ensure_ascii=False)
        ).where((Meals.id == meal_id) & (Meals.server_id == server_id)).execute()
    except Exception as e:
        wiz.response.status(500, message=str(e))

    wiz.response.status(200)

def delete_meal():
    role = wiz.session.get("role")
    if role not in ['teacher', 'director']:
        wiz.response.status(403, message="권한이 없습니다.")

    server_id = _get_server_id()
    meal_id = int(wiz.request.query("id", True))
    try:
        Meals.delete().where((Meals.id == meal_id) & (Meals.server_id == server_id)).execute()
    except Exception as e:
        wiz.response.status(500, message=str(e))

    wiz.response.status(200)

# 식단 안내 파일 관련
def get_meal_files():
    role = wiz.session.get("role")
    if not role:
        wiz.response.status(401, message="로그인이 필요합니다.")

    server_id = _get_server_id()
    fs = wiz.project.fs("data", "meal_files", str(server_id))
    meta_path = "meta.json"

    now = _now_kst()
    current_month = now.strftime("%Y-%m")
    if now.month == 12:
        next_month = f"{now.year + 1}-01"
    else:
        next_month = f"{now.year}-{str(now.month + 1).zfill(2)}"

    # 전체 파일을 월별로 그룹핑
    month_groups = {}
    try:
        if fs.exists(meta_path):
            meta = fs.read.json(meta_path, default=[])
            for f in meta:
                tm = f.get('target_month') or f.get('month', '') or current_month
                if tm not in month_groups:
                    month_groups[tm] = []
                month_groups[tm].append(f)
            for tm in month_groups:
                month_groups[tm].sort(key=lambda x: x.get('created_at', ''), reverse=True)
    except Exception:
        pass

    # 월 키를 역순 정렬 (최신월 먼저)
    sorted_months = sorted(month_groups.keys(), reverse=True)
    month_files = [{'month': m, 'files': month_groups[m]} for m in sorted_months]

    wiz.response.status(200, current_month=current_month, next_month=next_month,
        month_files=month_files)

def upload_meal_file():
    role = wiz.session.get("role")
    if role not in ['teacher', 'director']:
        wiz.response.status(403, message="권한이 없습니다.")

    file = wiz.request.file("file")
    if not file or not file.filename:
        wiz.response.status(400, message="파일을 선택해주세요.")

    server_id = _get_server_id()
    fs = wiz.project.fs("data", "meal_files", str(server_id))
    meta_path = "meta.json"

    original_name = file.filename
    ext = os.path.splitext(original_name)[1].lower()
    timestamp = str(_now_kst().timestamp()).replace(".", "")
    safe_name = timestamp + ext

    # 파일 원본 그대로 저장 (변환 없음)
    save_path = fs.abspath(safe_name)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, 'wb') as wf:
        wf.write(file.read())

    meta = []
    try:
        if fs.exists(meta_path):
            meta = fs.read.json(meta_path, default=[])
    except Exception:
        meta = []

    new_id = max([f.get('id', 0) for f in meta], default=0) + 1

    now = _now_kst()
    target_month = wiz.request.query("target_month", "")
    if not target_month:
        target_month = now.strftime("%Y-%m")

    meta.append({
        'id': new_id,
        'original_name': original_name,
        'file_name': safe_name,
        'target_month': target_month,
        'created_at': now.strftime("%Y-%m-%d %H:%M"),
        'created_by': wiz.session.get("id")
    })
    fs.write.json(meta_path, meta)

    wiz.response.status(200)

def delete_meal_file():
    role = wiz.session.get("role")
    if role not in ['teacher', 'director']:
        wiz.response.status(403, message="권한이 없습니다.")

    file_id = int(wiz.request.query("id", True))
    server_id = _get_server_id()
    fs = wiz.project.fs("data", "meal_files", str(server_id))
    meta_path = "meta.json"

    meta = []
    try:
        if fs.exists(meta_path):
            meta = fs.read.json(meta_path, default=[])
    except Exception:
        meta = []

    target = None
    for f in meta:
        if f.get('id') == file_id:
            target = f
            break

    if target:
        try:
            file_path = fs.abspath(target['file_name'])
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception:
            pass
        meta = [f for f in meta if f.get('id') != file_id]
        fs.write.json(meta_path, meta)

    wiz.response.status(200)

def serve_meal_file():
    role = wiz.session.get("role")
    if not role:
        wiz.response.status(401, message="로그인이 필요합니다.")

    file_id = int(wiz.request.query("id", True))
    server_id = _get_server_id()
    fs = wiz.project.fs("data", "meal_files", str(server_id))
    meta_path = "meta.json"

    meta = []
    try:
        if fs.exists(meta_path):
            meta = fs.read.json(meta_path, default=[])
    except Exception:
        meta = []

    target = None
    for f in meta:
        if f.get('id') == file_id:
            target = f
            break

    if not target:
        wiz.response.abort(404)

    filepath = fs.abspath(target['file_name'])
    if not os.path.isfile(filepath):
        wiz.response.abort(404)

    wiz.response.download(filepath, as_attachment=True, filename=target['original_name'])

# HWP 월간 식단 파일 상태 조회
def get_month_hwp():
    role = wiz.session.get("role")
    if not role:
        wiz.response.status(401, message="로그인이 필요합니다.")

    month = wiz.request.query("month", "")
    if not month:
        wiz.response.status(400, message="월 정보가 필요합니다.")

    server_id = _get_server_id()
    fs = wiz.project.fs("data", "meal_files", str(server_id))
    meta = []
    try:
        if fs.exists("meta.json"):
            meta = fs.read.json("meta.json", default=[])
    except Exception:
        meta = []

    hwp_file = None
    for f in meta:
        if f.get('month') == month and f.get('type') == 'hwp_meal':
            hwp_file = f
            break

    wiz.response.status(200, hwp_file=hwp_file)

# HWP 월간 식단 파일 삭제 + 해당 월 식단 전체 삭제
def delete_month_hwp():
    role = wiz.session.get("role")
    if role not in ['teacher', 'director']:
        wiz.response.status(403, message="권한이 없습니다.")

    month = wiz.request.query("month", True)
    server_id = _get_server_id()
    fs = wiz.project.fs("data", "meal_files", str(server_id))

    meta = []
    try:
        if fs.exists("meta.json"):
            meta = fs.read.json("meta.json", default=[])
    except Exception:
        meta = []

    # HWP 파일 삭제
    for f in meta:
        if f.get('month') == month and f.get('type') == 'hwp_meal':
            try:
                file_path = fs.abspath(f['file_name'])
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception:
                pass

    meta = [f for f in meta if not (f.get('month') == month and f.get('type') == 'hwp_meal')]
    fs.write.json("meta.json", meta)

    # 해당 월 식단 전체 삭제
    year, mon = month.split("-")
    year, mon = int(year), int(mon)
    start_date = datetime.date(year, mon, 1)
    if mon == 12:
        end_date = datetime.date(year + 1, 1, 1)
    else:
        end_date = datetime.date(year, mon + 1, 1)

    try:
        Meals.delete().where(
            (Meals.server_id == server_id) & (Meals.meal_date >= start_date) & (Meals.meal_date < end_date)
        ).execute()
    except Exception:
        pass

    wiz.response.status(200)

# HWP 식단표 파싱 → DB 자동 입력 (pyhwp XHTML 기반)
def _parse_meal_html(html_content, styles_css=''):
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html_content, 'html.parser')

    # CSS에서 초록색(#008000 등) charshape 클래스 식별
    green_charshapes = set()
    css_sources = [styles_css]
    for style_tag in soup.find_all('style'):
        css_sources.append(style_tag.get_text())
    for css_text in css_sources:
        if not css_text:
            continue
        for m in re.finditer(r'span\.(charshape-\d+)\s*\{[^}]*?color\s*:\s*(#[0-9a-fA-F]{3,6}|green)', css_text):
            cls, color = m.group(1), m.group(2).lower()
            if color in ('#008000', '#00ff00', '#006400', 'green', '#0f0', '#080'):
                green_charshapes.add(cls)

    tables = soup.find_all('table')

    year = None
    month = None
    meals = []
    daily_kcal = {}       # {date_str: {'12': kcal, '35': kcal}}
    daily_protein = {}    # {date_str: {'12': protein, '35': protein}}
    daily_theme = {}
    has_dual_age = False  # 1~2세/3~5세 양쪽 모두 있는 식단표인지

    meal_table = None
    for table in tables:
        rows = table.find_all('tr')
        if len(rows) < 5:
            continue
        first_text = rows[0].get_text()
        if re.search(r'\d{4}\s*년\s*\d{1,2}\s*월', first_text) and '식단' in first_text:
            meal_table = table
            break

    if not meal_table:
        return None, None, [], {}, {}

    rows = meal_table.find_all('tr')
    title_text = rows[0].get_text()
    match = re.search(r'(\d{4})\s*년\s*(\d{1,2})\s*월', title_text)
    if not match:
        return None, None, [], {}, {}

    year = int(match.group(1))
    month = int(match.group(2))

    # rowspan으로 점유된 셀 추적: (row_idx, col) → True
    occupied = {}

    def get_row_cells(ri, row):
        cells_data = []
        ci = 0
        for cell in row.find_all(['td', 'th']):
            while (ri, ci) in occupied:
                ci += 1
            colspan = int(cell.get('colspan', 1))
            rowspan = int(cell.get('rowspan', 1))
            paragraphs = cell.find_all('p')
            if paragraphs:
                p_texts = []
                for p in paragraphs:
                    if green_charshapes:
                        # span별로 초록색 여부 확인하여 마커 삽입
                        parts = []
                        for child in p.children:
                            if hasattr(child, 'get') and child.name == 'span':
                                span_classes = child.get('class', [])
                                is_green = any(c in green_charshapes for c in span_classes)
                                text = child.get_text(strip=True)
                                if text:
                                    if is_green:
                                        parts.append('{{green:' + text + '}}')
                                    else:
                                        parts.append(text)
                            elif hasattr(child, 'get_text'):
                                text = child.get_text(strip=True)
                                if text:
                                    parts.append(text)
                            else:
                                text = str(child).strip()
                                if text:
                                    parts.append(text)
                        line = ''.join(parts)
                    else:
                        line = p.get_text(strip=True)
                    if line:
                        p_texts.append(line)
                content = '\n'.join(p_texts)
            else:
                content = cell.get_text(separator='\n', strip=True)
            content = re.sub(r'\n+', '\n', content).strip()
            cells_data.append((ci, colspan, content))
            for dr in range(1, rowspan):
                for dc in range(colspan):
                    occupied[(ri + dr, ci + dc)] = True
            ci += colspan
        return cells_data

    current_date_map = {}

    for ri, row in enumerate(rows[1:], 1):
        cells_data = get_row_cells(ri, row)
        if not cells_data:
            continue

        first_col, first_cs, first_text = cells_data[0]
        first_clean = re.sub(r'\s+', '', first_text)

        if '일자' in first_clean:
            current_date_map = {}
            for col_start, colspan, text in cells_data[1:]:
                day_match = re.search(r'(\d{1,2})일', text)
                if day_match:
                    current_date_map[col_start] = int(day_match.group(1))

        elif current_date_map:
            meal_type = None
            is_kcal = False
            is_protein = False
            is_theme_row = False
            if '오전간식' in first_clean:
                meal_type = '오전간식'
            elif '오후간식' in first_clean:
                meal_type = '오후간식'
            elif '점심' in first_clean:
                meal_type = '점심'
            elif '열량' in first_clean or 'kcal' in first_clean.lower():
                is_kcal = True
            elif '단백질' in first_clean:
                is_protein = True
            elif '테마' in first_clean or '밥상' in first_clean:
                is_theme_row = True

            if is_theme_row:
                for col_start, colspan, text in cells_data[1:]:
                    if col_start in current_date_map:
                        day = current_date_map[col_start]
                        theme = _extract_theme(text)
                        if theme:
                            date_str = f'{year}-{month:02d}-{day:02d}'
                            daily_theme[date_str] = theme

            elif is_kcal:
                # 열량/단백질 행 파싱 — 두 가지 형식 처리:
                # (A) "열량/단백질" 합쳐진 행: 값이 "448/18" 형태
                #     - "1~2세", "3~5세" 라벨 셀이 앞에 올 수 있음 → 스킵
                #     - 라벨 있으면 값이 1~2세/3~5세 교대, 없으면 단일 연령
                # (B) "열량" 단독 행: 값이 숫자만 (기존 방식)
                is_combined = '단백질' in first_clean  # "열량/단백질" 합쳐진 형태
                data_cells = cells_data[1:]

                # 1~2세/3~5세 라벨 셀 감지 및 스킵
                label_count = 0
                for _, _, text in data_cells:
                    clean = re.sub(r'\s+', '', text)
                    if re.match(r'^[1-3][-~][2-5]세?$', clean):
                        label_count += 1
                        if '3' in clean or '5' in clean:
                            has_dual_age = True
                    else:
                        break
                if label_count > 0:
                    data_cells = data_cells[label_count:]

                # 날짜 순서 가져오기
                sorted_days = sorted(current_date_map.values())

                if has_dual_age:
                    # 값이 1~2세/3~5세 교대로 나옴
                    value_texts = [text for _, _, text in data_cells]
                    day_idx = 0
                    for vi in range(0, len(value_texts), 2):
                        if day_idx >= len(sorted_days):
                            break
                        day = sorted_days[day_idx]
                        date_str = f'{year}-{month:02d}-{day:02d}'

                        # 1~2세 값
                        val_12 = value_texts[vi] if vi < len(value_texts) else ''
                        # 3~5세 값
                        val_35 = value_texts[vi + 1] if vi + 1 < len(value_texts) else ''

                        if is_combined:
                            # "448/18" → kcal=448, protein=18
                            m12 = re.match(r'([\d,]+)\s*/\s*([\d,.]+)', val_12.replace(',', ''))
                            m35 = re.match(r'([\d,]+)\s*/\s*([\d,.]+)', val_35.replace(',', ''))
                            if m12:
                                k12 = int(m12.group(1))
                                p12 = float(m12.group(2))
                                if 100 <= k12 <= 5000:
                                    daily_kcal.setdefault(date_str, {})['12'] = k12
                                    daily_protein.setdefault(date_str, {})['12'] = p12
                            if m35:
                                k35 = int(m35.group(1))
                                p35 = float(m35.group(2))
                                if 100 <= k35 <= 5000:
                                    daily_kcal.setdefault(date_str, {})['35'] = k35
                                    daily_protein.setdefault(date_str, {})['35'] = p35
                        else:
                            # 열량만 있는 행
                            nm12 = re.search(r'[\d,]+', val_12.replace(',', ''))
                            nm35 = re.search(r'[\d,]+', val_35.replace(',', ''))
                            if nm12:
                                k12 = int(nm12.group().replace(',', ''))
                                if 100 <= k12 <= 5000:
                                    daily_kcal.setdefault(date_str, {})['12'] = k12
                            if nm35:
                                k35 = int(nm35.group().replace(',', ''))
                                if 100 <= k35 <= 5000:
                                    daily_kcal.setdefault(date_str, {})['35'] = k35
                        day_idx += 1
                else:
                    # 단일 연령 (기존 호환)
                    if is_combined:
                        value_texts = [text for _, _, text in data_cells]
                        for vi, val in enumerate(value_texts):
                            if vi >= len(sorted_days):
                                break
                            day = sorted_days[vi]
                            date_str = f'{year}-{month:02d}-{day:02d}'
                            m = re.match(r'([\d,]+)\s*/\s*([\d,.]+)', val.replace(',', ''))
                            if m:
                                k = int(m.group(1))
                                p = float(m.group(2))
                                if 100 <= k <= 5000:
                                    daily_kcal.setdefault(date_str, {})['12'] = k
                                    daily_protein.setdefault(date_str, {})['12'] = p
                    else:
                        for col_start, colspan, text in cells_data[1:]:
                            if col_start in current_date_map:
                                day = current_date_map[col_start]
                                num_match = re.search(r'[\d,]+', text.replace(',', ''))
                                if num_match:
                                    try:
                                        kcal_val = int(num_match.group().replace(',', ''))
                                        if 100 <= kcal_val <= 5000:
                                            date_str = f'{year}-{month:02d}-{day:02d}'
                                            daily_kcal.setdefault(date_str, {})['12'] = kcal_val
                                    except ValueError:
                                        pass

            elif is_protein:
                # 단백질 단독 행 (열량과 분리된 경우)
                data_cells = cells_data[1:]
                label_count = 0
                for _, _, text in data_cells:
                    clean = re.sub(r'\s+', '', text)
                    if re.match(r'^[1-3][-~][2-5]세?$', clean):
                        label_count += 1
                    else:
                        break
                if label_count > 0:
                    data_cells = data_cells[label_count:]
                sorted_days = sorted(current_date_map.values())

                if has_dual_age:
                    value_texts = [text for _, _, text in data_cells]
                    day_idx = 0
                    for vi in range(0, len(value_texts), 2):
                        if day_idx >= len(sorted_days):
                            break
                        day = sorted_days[day_idx]
                        date_str = f'{year}-{month:02d}-{day:02d}'
                        nm12 = re.search(r'[\d,.]+', value_texts[vi].replace(',', '') if vi < len(value_texts) else '')
                        nm35 = re.search(r'[\d,.]+', value_texts[vi + 1].replace(',', '') if vi + 1 < len(value_texts) else '')
                        if nm12:
                            daily_protein.setdefault(date_str, {})['12'] = float(nm12.group())
                        if nm35:
                            daily_protein.setdefault(date_str, {})['35'] = float(nm35.group())
                        day_idx += 1
                else:
                    value_texts = [text for _, _, text in data_cells]
                    for vi, val in enumerate(value_texts):
                        if vi >= len(sorted_days):
                            break
                        day = sorted_days[vi]
                        date_str = f'{year}-{month:02d}-{day:02d}'
                        nm = re.search(r'[\d,.]+', val.replace(',', ''))
                        if nm:
                            daily_protein.setdefault(date_str, {})['12'] = float(nm.group())

            elif meal_type:
                for col_start, colspan, text in cells_data[1:]:
                    if col_start in current_date_map:
                        day = current_date_map[col_start]
                        raw_content = text
                        if raw_content and '대체공휴일' not in raw_content:
                            allergy_nums = _extract_allergy_numbers(raw_content)
                            dish_allergy_map = _extract_dish_allergies(raw_content)
                            content = _clean_meal_content(raw_content)
                            if content:
                                try:
                                    date_str = f'{year}-{month:02d}-{day:02d}'
                                    datetime.date.fromisoformat(date_str)
                                    # 점심 내용에서 테마 키워드 추출
                                    if meal_type == '점심' and date_str not in daily_theme:
                                        theme = _extract_theme(raw_content)
                                        if theme:
                                            daily_theme[date_str] = theme
                                    meals.append({
                                        'date': date_str,
                                        'meal_type': meal_type,
                                        'content': content,
                                        'allergy_numbers': allergy_nums,
                                        'dish_allergies': dish_allergy_map
                                    })
                                except ValueError:
                                    pass

    return year, month, meals, daily_kcal, daily_protein, daily_theme

def parse_hwp_meal():
    role = wiz.session.get("role")
    if role not in ['teacher', 'director']:
        wiz.response.status(403, message="권한이 없습니다.")

    server_id = _get_server_id()
    user_id = wiz.session.get("id")
    file = wiz.request.file("file")
    if not file or not file.filename:
        wiz.response.status(400, message="파일을 선택해주세요.")

    original_name = file.filename
    ext = os.path.splitext(original_name)[1].lower()
    if ext not in ['.hwp', '.hwpx']:
        wiz.response.status(400, message=f"HWP/HWPX 파일만 지원합니다. (받은 파일: {original_name})")

    fs = wiz.project.fs("data", "meal_files", str(server_id))
    timestamp = str(_now_kst().timestamp()).replace(".", "")
    file_name = timestamp + ext

    # HWP 파일 저장 (영구 보관)
    file_data = file.read()
    saved_path = fs.abspath(file_name)
    outdir = fs.abspath("")
    os.makedirs(outdir, exist_ok=True)
    with open(saved_path, 'wb') as wf:
        wf.write(file_data)

    if not os.path.isfile(saved_path):
        wiz.response.status(500, message="파일 저장에 실패했습니다.")

    # pyhwp(hwp5html)로 XHTML 변환
    convert_error = None
    html_content = ""
    tmp_outdir = tempfile.mkdtemp(prefix="hwp_")
    try:
        result = subprocess.run(
            ['hwp5html', '--output', tmp_outdir, saved_path],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            convert_error = result.stderr or "hwp5html 변환 실패"
    except Exception as e:
        convert_error = str(e)

    if not convert_error:
        xhtml_path = os.path.join(tmp_outdir, 'index.xhtml')
        if os.path.isfile(xhtml_path):
            try:
                with open(xhtml_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
            except Exception as e:
                convert_error = f"XHTML 읽기 오류: {str(e)}"
        else:
            convert_error = "XHTML 파일이 생성되지 않았습니다."

    # styles.css 읽기 (초록색 텍스트 감지용)
    styles_css = ''
    if not convert_error:
        styles_path = os.path.join(tmp_outdir, 'styles.css')
        if os.path.isfile(styles_path):
            try:
                with open(styles_path, 'r', encoding='utf-8') as f:
                    styles_css = f.read()
            except Exception:
                pass

    shutil.rmtree(tmp_outdir, ignore_errors=True)

    if convert_error:
        try:
            os.remove(saved_path)
        except Exception:
            pass
        wiz.response.status(500, message=convert_error)

    year, month, meals, daily_kcal, daily_protein, daily_theme = _parse_meal_html(html_content, styles_css)

    if not meals:
        try:
            os.remove(saved_path)
        except Exception:
            pass
        wiz.response.status(400, message="식단 데이터를 추출할 수 없습니다. 식단표 형식을 확인해주세요.")

    month_str = f"{year}-{month:02d}"

    # 해당 월의 기존 식단 삭제
    start_date = datetime.date(year, month, 1)
    if month == 12:
        end_date = datetime.date(year + 1, 1, 1)
    else:
        end_date = datetime.date(year, month + 1, 1)

    try:
        Meals.delete().where(
            (Meals.server_id == server_id) & (Meals.meal_date >= start_date) & (Meals.meal_date < end_date)
        ).execute()
    except Exception:
        pass

    # 새 식단 입력
    inserted = 0
    for meal in meals:
        try:
            kcal_data = daily_kcal.get(meal['date'], {})
            protein_data = daily_protein.get(meal['date'], {})
            # 점심 행에만 열량/단백질 저장 (일일 합계)
            meal_kcal = kcal_data.get('12') if meal['meal_type'] == '점심' else None
            meal_protein = protein_data.get('12') if meal['meal_type'] == '점심' else None
            meal_kcal_35 = kcal_data.get('35') if meal['meal_type'] == '점심' else None
            meal_protein_35 = protein_data.get('35') if meal['meal_type'] == '점심' else None
            meal_theme = daily_theme.get(meal['date'])
            Meals.create(
                server_id=server_id,
                meal_type=meal['meal_type'],
                meal_date=meal['date'],
                content=meal['content'],
                allergy_numbers=json.dumps(meal.get('allergy_numbers', [])),
                dish_allergies=json.dumps(meal.get('dish_allergies', {}), ensure_ascii=False),
                theme=meal_theme,
                kcal=meal_kcal,
                protein=meal_protein,
                kcal_35=meal_kcal_35,
                protein_35=meal_protein_35,
                photo_path='',
                created_by=user_id
            )
            inserted += 1
        except Exception:
            pass

    # meta.json에 월별 HWP 기록 (기존 동일 월 항목 교체)
    meta = []
    try:
        if fs.exists("meta.json"):
            meta = fs.read.json("meta.json", default=[])
    except Exception:
        meta = []

    # 기존 동일 월 HWP 삭제
    for old in meta:
        if old.get('month') == month_str and old.get('type') == 'hwp_meal':
            try:
                old_path = fs.abspath(old['file_name'])
                if os.path.isfile(old_path):
                    os.remove(old_path)
            except Exception:
                pass
    meta = [m for m in meta if not (m.get('month') == month_str and m.get('type') == 'hwp_meal')]

    new_id = max([f.get('id', 0) for f in meta], default=0) + 1
    meta.append({
        'id': new_id,
        'original_name': original_name,
        'file_name': file_name,
        'month': month_str,
        'type': 'hwp_meal',
        'created_at': _now_kst().strftime("%Y-%m-%d %H:%M"),
        'created_by': user_id
    })
    fs.write.json("meta.json", meta)

    wiz.response.status(200, year=year, month=month, count=inserted)

# ===== 식단 통계 =====
# 기존에 저장된 HWP 파일을 재파싱하여 theme/green 마커 업데이트
def reparse_stored_hwp():
    role = wiz.session.get("role")
    if role not in ['teacher', 'director']:
        wiz.response.status(403, message="권한이 없습니다.")

    server_id = _get_server_id()
    fs = wiz.project.fs("data", "meal_files", str(server_id))

    meta = []
    try:
        if fs.exists("meta.json"):
            meta = fs.read.json("meta.json", default=[])
    except Exception:
        wiz.response.status(200, updated=0, message="meta.json 없음")

    hwp_meta = [m for m in meta if m.get('type') == 'hwp_meal']
    if not hwp_meta:
        wiz.response.status(200, updated=0, message="저장된 HWP 파일이 없습니다.")

    total_updated = 0
    errors = []
    for entry in hwp_meta:
        hwp_path = fs.abspath(entry['file_name'])
        if not os.path.isfile(hwp_path):
            errors.append(f"{entry['file_name']}: 파일 없음")
            continue

        # hwp5html로 변환
        tmp_outdir = tempfile.mkdtemp(prefix="hwp_reparse_")
        html_content = ''
        styles_css = ''
        try:
            result = subprocess.run(
                ['hwp5html', '--output', tmp_outdir, hwp_path],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                xhtml_path = os.path.join(tmp_outdir, 'index.xhtml')
                styles_path = os.path.join(tmp_outdir, 'styles.css')
                if os.path.isfile(xhtml_path):
                    with open(xhtml_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                if os.path.isfile(styles_path):
                    with open(styles_path, 'r', encoding='utf-8') as f:
                        styles_css = f.read()
        except Exception as e:
            errors.append(f"{entry['file_name']}: 변환 실패 - {str(e)}")
        finally:
            shutil.rmtree(tmp_outdir, ignore_errors=True)

        if not html_content:
            continue

        year, month, meals, daily_kcal, daily_protein, daily_theme = _parse_meal_html(html_content, styles_css)
        if not meals:
            errors.append(f"{entry['file_name']}: 식단 파싱 실패")
            continue

        # DB 업데이트: 해당 월의 기존 레코드에 theme, content(green 마커 포함) 업데이트
        updated = 0
        for meal in meals:
            try:
                kcal_data = daily_kcal.get(meal['date'], {})
                protein_data = daily_protein.get(meal['date'], {})
                meal_kcal = kcal_data.get('12') if meal['meal_type'] == '점심' else None
                meal_protein = protein_data.get('12') if meal['meal_type'] == '점심' else None
                meal_kcal_35 = kcal_data.get('35') if meal['meal_type'] == '점심' else None
                meal_protein_35 = protein_data.get('35') if meal['meal_type'] == '점심' else None
                meal_theme = daily_theme.get(meal['date'])
                rows_updated = Meals.update(
                    content=meal['content'],
                    theme=meal_theme,
                    kcal=meal_kcal if meal_kcal else Meals.kcal,
                    protein=meal_protein if meal_protein else Meals.protein,
                    kcal_35=meal_kcal_35 if meal_kcal_35 else Meals.kcal_35,
                    protein_35=meal_protein_35 if meal_protein_35 else Meals.protein_35,
                    allergy_numbers=json.dumps(meal.get('allergy_numbers', [])),
                    dish_allergies=json.dumps(meal.get('dish_allergies', {}), ensure_ascii=False)
                ).where(
                    (Meals.server_id == server_id) &
                    (Meals.meal_date == meal['date']) &
                    (Meals.meal_type == meal['meal_type'])
                ).execute()
                updated += rows_updated
            except Exception:
                pass
        total_updated += updated

    wiz.response.status(200, updated=total_updated, errors=errors,
                        message=f"{total_updated}개 식단 레코드가 업데이트되었습니다.")

# 어린이집 제공분 기준 영양 목표 — nutrition_api 공유 상수 사용

def get_stats():
    role = wiz.session.get("role")
    if not role:
        wiz.response.status(401, message="로그인이 필요합니다.")

    server_id = _get_server_id()
    month = wiz.request.query("month", "")
    if not month:
        month = datetime.date.today().strftime("%Y-%m")
    selected_age = wiz.request.query("age", "1~2세")

    year, mon = month.split("-")
    year = int(year)
    mon = int(mon)

    start_date = datetime.date(year, mon, 1)
    if mon == 12:
        end_date = datetime.date(year + 1, 1, 1)
    else:
        end_date = datetime.date(year, mon + 1, 1)

    # 일자별 식단 수집
    daily_meals = {}
    daily_calories = {}
    total_meals = 0

    try:
        rows = list(Meals.select().where(
            (Meals.server_id == server_id) &
            (Meals.meal_date >= start_date) &
            (Meals.meal_date < end_date)
        ).order_by(Meals.meal_date))
        for row in rows:
            total_meals += 1
            date_str = row.meal_date.strftime("%Y-%m-%d") if hasattr(row.meal_date, 'strftime') else str(row.meal_date)
            if date_str not in daily_meals:
                daily_meals[date_str] = []
            daily_meals[date_str].append({
                'meal_type': row.meal_type or '기타',
                'content': row.content or ''
            })
            # 선택된 연령에 맞는 칼로리 사용
            if selected_age == '3~5세' and row.kcal_35 and row.kcal_35 > 0:
                daily_calories[date_str] = row.kcal_35
            elif row.kcal and row.kcal > 0:
                daily_calories[date_str] = row.kcal
    except Exception as e:
        wiz.response.status(500, message=str(e))

    # 통합 스케일링으로 일별 칼로리 보완 (병렬)
    api_daily_calories = {}
    try:
        nutrition_api = wiz.model("nutrition_api")
        from concurrent.futures import ThreadPoolExecutor

        # DB에 kcal 없는 날의 모든 끼니를 병렬 조회
        missing_dates = {d: dm for d, dm in daily_meals.items() if d not in daily_calories}
        all_tasks = []
        for date_str, day_meals in missing_dates.items():
            for m in day_meals:
                all_tasks.append((date_str, m['meal_type'], m['content']))

        results_by_date = {d: 0 for d in missing_dates}
        if all_tasks:
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = {executor.submit(nutrition_api.search_meal, content, selected_age): (date_str, meal_type) for date_str, meal_type, content in all_tasks}
                for future in futures:
                    date_str, meal_type = futures[future]
                    try:
                        meal_result = future.result()
                        scaled = nutrition_api.compute_scaled_nutrients(meal_result, meal_type, selected_age)
                        results_by_date[date_str] += scaled.get('calories', 0)
                    except Exception:
                        pass

            for date_str, kcal in results_by_date.items():
                if kcal > 0:
                    api_daily_calories[date_str] = round(kcal)
    except Exception:
        pass

    # DB kcal 우선 + API kcal 보완
    merged_calories = dict(api_daily_calories)
    merged_calories.update(daily_calories)  # DB kcal이 우선

    # shared targets 참조
    nutrition_api = wiz.model("nutrition_api")
    _TARGETS = nutrition_api.DAYCARE_TARGETS
    DAYCARE_TARGET = _TARGETS.get(selected_age, _TARGETS['1~2세'])
    target_kcal = DAYCARE_TARGET['calories']['value']

    # 간단 AGE_NUTRITION (프론트 하위호환)
    AGE_NUTRITION = {}
    for age_key, targets in _TARGETS.items():
        AGE_NUTRITION[age_key] = {
            'kcal': targets['calories']['value'],
            'protein': targets['protein']['value'],
            'calcium': targets['calcium']['value'],
        }

    wiz.response.status(200,
        month=month,
        total_meals=total_meals,
        total_days=len(daily_meals),
        daily_meals=daily_meals,
        daily_calories=merged_calories,
        target_kcal=target_kcal,
        age_nutrition=AGE_NUTRITION,
        ages=list(_TARGETS.keys()),
        selected_age=selected_age
    )

# ===== 부모용 맞춤 통계 =====
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

def get_parent_stats():
    role = wiz.session.get("role")
    if not role:
        wiz.response.status(401, message="로그인이 필요합니다.")

    user_id = int(wiz.session.get("id"))
    server_id = _get_server_id()

    # 역할별 자녀 목록 조회 (children_rows + class_name 매핑)
    children_rows = []
    child_class_map = {}  # child.id → class_name

    if role == 'parent':
        children_rows = list(Children.select().where(Children.user_id == user_id))
    elif role in ('director', 'teacher'):
        # 서버 소속 학부모 조회
        server_user_ids = []
        try:
            members = ServerMembers.select(ServerMembers.user_id).where(
                ServerMembers.server_id == server_id
            )
            server_user_ids = [m.user_id for m in members]
        except Exception:
            pass

        teacher_class = ""
        if role == 'teacher':
            try:
                me = Users.select(Users.class_name).where(Users.id == user_id).first()
                if me and me.class_name:
                    teacher_class = me.class_name.strip()
            except Exception:
                pass

        if server_user_ids:
            try:
                query = Users.select(Users.id, Users.class_name).where(
                    Users.id.in_(server_user_ids),
                    Users.role == "parent",
                    Users.approved == True
                )
                if role == 'teacher' and teacher_class:
                    query = query.where(Users.class_name == teacher_class)
                parents = list(query)
                for parent in parents:
                    pclass = (parent.class_name or "").strip()
                    try:
                        parent_children = list(Children.select().where(Children.user_id == parent.id))
                        for child in parent_children:
                            children_rows.append(child)
                            child_class_map[child.id] = pclass
                    except Exception:
                        pass
            except Exception:
                pass

    if not children_rows:
        wiz.response.status(200, children=[])

    today = _now_kst().date()
    monday = today - datetime.timedelta(days=today.weekday())
    sunday = monday + datetime.timedelta(days=6)

    # 이번 주 식단 조회
    week_meals = list(Meals.select().where(
        (Meals.server_id == server_id) &
        (Meals.meal_date >= monday) &
        (Meals.meal_date <= sunday)
    ).order_by(Meals.meal_date))

    # 이번 주 알레르기 번호 + content 수집
    week_allergy_nums = set()
    week_content = ""
    week_meal_data = {}
    for m in week_meals:
        date_str = m.meal_date.strftime("%Y-%m-%d") if hasattr(m.meal_date, 'strftime') else str(m.meal_date)
        if date_str not in week_meal_data:
            week_meal_data[date_str] = []
        # dish_allergies 파싱
        dish_allergy_map = {}
        if m.dish_allergies:
            try:
                dish_allergy_map = json.loads(m.dish_allergies)
            except Exception:
                pass
        week_meal_data[date_str].append({
            'meal_type': m.meal_type or '기타',
            'content': m.content or '',
            'allergy_numbers': json.loads(m.allergy_numbers) if m.allergy_numbers else [],
            'dish_allergies': dish_allergy_map
        })
        week_content += " " + (m.content or "")
        if m.allergy_numbers:
            try:
                week_allergy_nums.update(json.loads(m.allergy_numbers))
            except Exception:
                pass

    # 주의식품 키워드 매핑
    num_to_foods = {}
    try:
        for cat in AllergyCategories.select():
            try:
                numbers = json.loads(cat.allergy_numbers) if cat.allergy_numbers else []
            except Exception:
                numbers = []
            raw_foods = (cat.caution_foods or '').replace('(', ',').replace(')', ',')
            foods = [f.strip() for f in raw_foods.split(',') if f.strip()]
            for num in numbers:
                if num not in num_to_foods:
                    num_to_foods[num] = []
                num_to_foods[num].extend(foods)
    except Exception:
        pass

    result_children = []
    # 연령별 목표 열량 매핑
    _nutrition_ref = wiz.model("nutrition_api")
    _TARGETS = _nutrition_ref.DAYCARE_TARGETS
    AGE_KCAL = {age: t['calories']['value'] for age, t in _TARGETS.items()}

    for child in children_rows:
        # 연령 계산
        age_years = (today - child.birthdate).days // 365 if child.birthdate else 3
        age_group = '3~5세' if age_years >= 3 else '1~2세'
        target_kcal = AGE_KCAL.get(age_group, 420)

        # 자녀 알레르기 조회
        child_allergies = list(ChildAllergies.select().where(ChildAllergies.child_id == child.id))
        child_allergy_nums = set()
        allergy_types = []
        other_keywords = []  # 기타 알레르기의 상세 키워드
        for ca in child_allergies:
            if ca.allergy_type == '기타' and ca.other_detail:
                detail = ca.other_detail.strip()
                allergy_types.append(f"기타({detail})")
                # 키워드 파싱
                for kw in detail.replace('/', ',').split(','):
                    kw = kw.strip()
                    if kw:
                        other_keywords.append(kw)
            else:
                allergy_types.append(ca.allergy_type)
            if ca.allergy_type == '기타' and ca.other_detail:
                detail_text = ca.other_detail.strip()
                found = ALLERGY_TYPE_TO_NUMBERS.get(detail_text, [])
                if found:
                    child_allergy_nums.update(found)
                else:
                    for part in re.split(r'[,\s/]+', detail_text):
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

        # 이번 주 알레르기 매칭 일자 + 식단명
        allergy_days = []
        has_standard_match = bool(week_allergy_nums & child_allergy_nums)
        has_other_match = bool(other_keywords)

        if has_standard_match or has_other_match:
            for date_str, day_meals in sorted(week_meal_data.items()):
                day_matched = []
                for meal in day_meals:
                    meal_nums = set(meal['allergy_numbers'])
                    dish_allergy_map = meal.get('dish_allergies', {})
                    # 식단 content에서 개별 음식명 추출 (green 마커 제거)
                    raw_content = re.sub(r'\{\{green:(.*?)\}\}', r'\1', meal['content'])
                    dishes = [d.strip() for d in re.split(r'[,\n/]', raw_content) if d.strip()]
                    dishes = [re.sub(r'[\u2460-\u2473\u3251-\u325f\d.]+$', '', d).strip() for d in dishes]
                    dishes = [d for d in dishes if d]

                    # dish_allergies가 있으면 정확한 매칭 사용
                    if dish_allergy_map:
                        # 표준 알레르기: 각 음식의 번호와 자녀 알레르기 번호 비교
                        for dish_name, dish_nums in dish_allergy_map.items():
                            clean_dish = re.sub(r'\{\{green:(.*?)\}\}', r'\1', dish_name)
                            overlap = set(dish_nums) & child_allergy_nums
                            if overlap:
                                anames = set()
                                for num in overlap:
                                    anames.add(ALLERGY_MAP.get(num, str(num)))
                                for aname in anames:
                                    entry = {'dish': clean_dish, 'allergy': aname}
                                    if entry not in day_matched:
                                        day_matched.append(entry)
                        # 기타 알레르기: 키워드 매칭
                        for kw in other_keywords:
                            for dish in dishes:
                                if _keyword_in_content(kw, dish):
                                    entry = {'dish': dish, 'allergy': kw}
                                    if entry not in day_matched:
                                        day_matched.append(entry)
                    else:
                        # fallback: 기존 키워드 매칭 (dish_allergies 없는 이전 데이터)
                        overlap = meal_nums & child_allergy_nums
                        if overlap:
                            for num in overlap:
                                keywords = num_to_foods.get(num, [])
                                aname = ALLERGY_MAP.get(num, str(num))
                                found_dish = False
                                for dish in dishes:
                                    matched = False
                                    for kw in keywords:
                                        if _keyword_in_content(kw, dish):
                                            matched = True
                                            break
                                    if matched and {'dish': dish, 'allergy': aname} not in day_matched:
                                        day_matched.append({'dish': dish, 'allergy': aname})
                                        found_dish = True
                                if not found_dish:
                                    day_matched.append({'dish': '', 'allergy': aname})

                        # 기타 알레르기 키워드 매칭
                        for kw in other_keywords:
                            for dish in dishes:
                                if _keyword_in_content(kw, dish) and {'dish': dish, 'allergy': kw} not in day_matched:
                                    day_matched.append({'dish': dish, 'allergy': kw})

                if day_matched:
                    allergy_days.append({'date': date_str, 'items': day_matched})

        result_children.append({
            'name': child.name,
            'class_name': child_class_map.get(child.id, ''),
            'age_group': age_group,
            'target_kcal': target_kcal,
            'allergy_types': allergy_types,
            'allergy_days': allergy_days,
        })

    # 이번 주 알레르기 매칭이 없는 아이는 제외
    result_children = [c for c in result_children if c['allergy_days']]

    wiz.response.status(200,
        children=result_children,
        week_start=monday.strftime("%Y-%m-%d"),
        week_end=sunday.strftime("%Y-%m-%d")
    )

# ===== 식단 AI 분석 (별도 호출, 캐싱 적용) =====
def _ai_cache_path(server_id, month):
    """AI 분석 결과 캐시 파일 경로"""
    return wiz.project.fs("data", "meal_ai_cache", str(server_id))

def _get_meal_data_hash(server_id, month):
    """해당 월 식단 데이터의 총 건수+내용 해시 → 식단 변경 감지용"""
    import hashlib
    year, mon = month.split("-")
    year, mon = int(year), int(mon)
    start_date = datetime.date(year, mon, 1)
    end_date = datetime.date(year + 1, 1, 1) if mon == 12 else datetime.date(year, mon + 1, 1)
    content_parts = []
    try:
        rows = list(Meals.select().where(
            (Meals.server_id == server_id) &
            (Meals.meal_date >= start_date) &
            (Meals.meal_date < end_date)
        ).order_by(Meals.meal_date, Meals.id))
        for row in rows:
            content_parts.append(f"{row.meal_date}|{row.meal_type}|{row.content}|{row.kcal}")
    except Exception:
        pass
    raw = "\n".join(content_parts)
    return hashlib.md5(raw.encode()).hexdigest()

def get_ai_analysis():
    role = wiz.session.get("role")
    if not role:
        wiz.response.status(401, message="로그인이 필요합니다.")

    server_id = _get_server_id()
    month = wiz.request.query("month", "")
    if not month:
        month = datetime.date.today().strftime("%Y-%m")
    refresh = wiz.request.query("refresh", "false") == "true"

    year, mon = month.split("-")
    year = int(year)
    mon = int(mon)

    # 캐시 확인
    cache_fs = _ai_cache_path(server_id, month)
    cache_file = f"{month}.json"
    data_hash = _get_meal_data_hash(server_id, month)

    if not refresh:
        try:
            if cache_fs.exists(cache_file):
                cached = cache_fs.read.json(cache_file, default=None)
                if cached:
                    print(f"캐시 사용됨: {month}")
                    data_changed = cached.get("data_hash") != data_hash
                    wiz.response.status(200,
                        nutrients=cached.get("nutrients", {}),
                        deficient_nutrients=cached.get("deficient_nutrients", []),
                        summary=cached.get("summary", ""),
                        cached=True,
                        cached_at=cached.get("cached_at", ""),
                        data_changed=data_changed
                    )
        except Exception:
            pass

    start_date = datetime.date(year, mon, 1)
    if mon == 12:
        end_date = datetime.date(year + 1, 1, 1)
    else:
        end_date = datetime.date(year, mon + 1, 1)

    daily_meals = {}
    db_daily_kcal = {}
    try:
        rows = list(Meals.select().where(
            (Meals.server_id == server_id) &
            (Meals.meal_date >= start_date) &
            (Meals.meal_date < end_date)
        ).order_by(Meals.meal_date))
        for row in rows:
            date_str = row.meal_date.strftime("%Y-%m-%d") if hasattr(row.meal_date, 'strftime') else str(row.meal_date)
            if date_str not in daily_meals:
                daily_meals[date_str] = []
            daily_meals[date_str].append({
                'meal_type': row.meal_type or '기타',
                'content': row.content or ''
            })
            if row.kcal and row.kcal > 0:
                db_daily_kcal[date_str] = row.kcal
    except Exception as e:
        wiz.response.status(500, message=str(e))

    if not daily_meals:
        wiz.response.status(200, nutrients={}, deficient_nutrients=[], summary="")

    # 연령별 어린이집 제공분 (점심+간식2회) 하루 영양 기준 — 공유 상수 참조
    nutrition_api = wiz.model("nutrition_api")
    selected_age = "1~2세"
    _TARGETS = nutrition_api.DAYCARE_TARGETS
    DAYCARE_TARGET = _TARGETS.get(selected_age, _TARGETS['1~2세'])
    DISPLAY_NAMES = nutrition_api.DISPLAY_NAMES

    # 식약처 API 기반 월간 영양소 합산 (스케일링 적용, 병렬 조회)
    month_total = {k: 0.0 for k in DAYCARE_TARGET}
    num_days = len(daily_meals)

    try:
        from concurrent.futures import ThreadPoolExecutor

        # 모든 끼니의 content를 한 번에 병렬 조회
        all_tasks = []
        for date_str in sorted(daily_meals.keys()):
            day_kcal = db_daily_kcal.get(date_str)
            for m in daily_meals[date_str]:
                all_tasks.append((date_str, m['meal_type'], m['content'], day_kcal))

        # 병렬 search_meal
        search_results = {}
        if all_tasks:
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = {}
                for i, (date_str, meal_type, content, day_kcal) in enumerate(all_tasks):
                    futures[executor.submit(nutrition_api.search_meal, content, selected_age)] = i
                for future in futures:
                    idx = futures[future]
                    try:
                        search_results[idx] = future.result()
                    except Exception:
                        search_results[idx] = {'menus': [], 'total': {}, 'found_count': 0, 'total_count': 0}

        # 결과 합산 (순서 유지) — 통합 스케일링 적용
        for i, (date_str, meal_type, content, day_kcal) in enumerate(all_tasks):
            meal_result = search_results.get(i, {'menus': [], 'total': {}, 'found_count': 0, 'total_count': 0})
            scaled = nutrition_api.compute_scaled_nutrients(meal_result, meal_type, selected_age, day_kcal if meal_type == '점심' else None)
            for k in month_total:
                month_total[k] += scaled.get(k, 0)
    except Exception:
        pass

    # 달성률 계산: 실제 합산 / (하루 기준 × 등원일수) × 100
    nutrients = {}
    deficient_nutrients = []

    for key in DAYCARE_TARGET:
        target_per_day = DAYCARE_TARGET[key]['value']
        total_target = target_per_day * num_days
        actual = month_total.get(key, 0)

        if total_target > 0:
            percent = min(round((actual / total_target) * 100), 100)
        else:
            percent = 0

        status = "양호" if percent >= 80 else "부족"
        display_name = DISPLAY_NAMES[key]

        nutrients[display_name] = {
            'percent': percent,
            'target': DAYCARE_TARGET[key]['label'],
            'status': status
        }

        if percent < 80:
            deficient_nutrients.append({
                'name': display_name,
                'percent': percent,
                'target': DAYCARE_TARGET[key]['label']
            })

    # AI: 부족 영양소 보충 조언 + 종합 평가만 요청
    summary = ""
    if deficient_nutrients:
        deficient_text = "\n".join([f"- {d['name']}: 달성률 {d['percent']}% (기준: {d['target']})" for d in deficient_nutrients])
        prompt = f"""{year}년 {mon}월 1-2세 어린이집 식단(점심+간식2회) 분석 결과, 아래 영양소가 부족합니다:
{deficient_text}

등원일수: {num_days}일

각 부족 영양소에 대해 보충 조언(advice)과 관련 음식 이모지(emoji)를 제공하고,
전체 종합 평가(summary)를 1-2문장으로 작성해주세요.

JSON 형식:
{{"deficient_advice": [{{"name": "영양소명", "emoji": "🍊", "advice": "구체적 보충 조언"}}], "summary": "종합 평가"}}"""

        try:
            gemini = wiz.model("gemini")
            ai_result = gemini.ask_json(prompt, system_instruction="어린이 영양사입니다. 서버가 계산한 부족 영양소 기준만으로 advice만 작성하세요. JSON만 응답하세요.")
            if isinstance(ai_result, dict):
                for da in ai_result.get('deficient_advice', []):
                    for dn in deficient_nutrients:
                        if dn['name'] == da.get('name'):
                            dn['emoji'] = da.get('emoji', '📊')
                            dn['advice'] = da.get('advice', '')
                summary = ai_result.get('summary', '')
        except Exception:
            pass

        # AI 응답 없는 항목에 기본값
        for dn in deficient_nutrients:
            if 'emoji' not in dn:
                dn['emoji'] = '📊'
            if 'advice' not in dn:
                dn['advice'] = f"{dn['name']} 섭취가 부족합니다. 관련 식품을 보충해주세요."
        if not summary:
            names = ", ".join([d['name'] for d in deficient_nutrients])
            summary = f"이번 달 식단에서 {names}의 섭취가 부족합니다. 가정에서 보충 식품을 제공해주세요."
    else:
        summary = f"이번 달 어린이집 식단({num_days}일)의 영양 균형이 전반적으로 양호합니다."

    # 캐시 저장
    try:
        cache_data = {
            "data_hash": data_hash,
            "cached_at": _now_kst().strftime("%Y-%m-%d %H:%M"),
            "nutrients": nutrients,
            "deficient_nutrients": deficient_nutrients,
            "summary": summary
        }
        cache_fs.write.json(cache_file, cache_data)
    except Exception:
        pass

    wiz.response.status(200,
        nutrients=nutrients,
        deficient_nutrients=deficient_nutrients,
        summary=summary,
        cached=False
    )
