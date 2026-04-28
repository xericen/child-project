# pyright: reportUndefinedVariable=false, reportMissingImports=false
import datetime
import json
from concurrent.futures import ThreadPoolExecutor

KST = datetime.timezone(datetime.timedelta(hours=9))
Meals = wiz.model("db/childcheck/meals")
Users = wiz.model("db/login_db/users")
Children = wiz.model("db/childcheck/children")
ChildAllergies = wiz.model("db/childcheck/child_allergies")
ServerMembers = wiz.model("db/login_db/server_members")
NutritionMapping = wiz.model("db/childcheck/nutrition_mapping")

# 공유 상수는 nutrition_api 인스턴스를 통해 접근
_nutrition_api_ref = wiz.model("nutrition_api")
DAYCARE_TARGETS = _nutrition_api_ref.DAYCARE_TARGETS
DISPLAY_NAMES = _nutrition_api_ref.DISPLAY_NAMES

def _now_kst():
    return datetime.datetime.now(KST)

def _get_server_id():
    server_id = wiz.request.query("server_id", "")
    if not server_id:
        server_id = wiz.session.get("server_id")
    return server_id

def get_role():
    role = wiz.session.get("role")
    if not role:
        wiz.response.status(401, message="로그인이 필요합니다.")
    wiz.response.status(200, role=role)

def get_dashboard():
    """대시보드 종합 데이터: 월간 영양소 충족률 + 일별 열량 추이 + 부족 영양소 + AI 요약"""
    role = wiz.session.get("role")
    if not role:
        wiz.response.status(401, message="로그인이 필요합니다.")

    server_id = _get_server_id()
    month = wiz.request.query("month", "")
    if not month:
        month = _now_kst().strftime("%Y-%m")

    # 연령 그룹 결정: 파라미터 > 부모 자녀 나이 > 기본값
    selected_age = wiz.request.query("age", "")
    if not selected_age:
        if role == "parent":
            user_id = wiz.session.get("id")
            if user_id:
                try:
                    today = _now_kst().date()
                    children = list(Children.select().where(Children.user_id == int(user_id)))
                    if children:
                        child = children[0]
                        if child.birthdate:
                            age = today.year - child.birthdate.year
                            if (today.month, today.day) < (child.birthdate.month, child.birthdate.day):
                                age -= 1
                            selected_age = "3~5세" if age >= 3 else "1~2세"
                except Exception:
                    pass
        if not selected_age:
            selected_age = "1~2세"

    refresh = wiz.request.query("refresh", "false") == "true"

    year, mon = month.split("-")
    year, mon = int(year), int(mon)

    # 캐시 확인
    cache_fs = wiz.project.fs("data", "nutrition_dashboard_cache", str(server_id))
    cache_file = f"{month}_{selected_age}.json"

    if not refresh:
        try:
            if cache_fs.exists(cache_file):
                cached = cache_fs.read.json(cache_file, default=None)
                if cached:
                    wiz.response.status(200, **cached, cached=True)
        except Exception:
            pass

    start_date = datetime.date(year, mon, 1)
    end_date = datetime.date(year + 1, 1, 1) if mon == 12 else datetime.date(year, mon + 1, 1)

    # DB에서 월간 식단 조회
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
            # 연령에 따라 적절한 DB kcal 사용
            kcal_val = None
            if selected_age == "3~5세":
                try:
                    kcal_val = row.kcal_35
                except Exception:
                    pass
            if not kcal_val or kcal_val <= 0:
                kcal_val = row.kcal if hasattr(row, 'kcal') else None
            if kcal_val and kcal_val > 0:
                db_daily_kcal[date_str] = kcal_val
    except Exception as e:
        wiz.response.status(500, message=str(e))

    if not daily_meals:
        wiz.response.status(200,
            month=month, age=selected_age, total_days=0,
            daily_calories={}, nutrients={}, deficient_nutrients=[],
            summary="해당 월 식단 데이터가 없습니다.", nutrient_daily={}, cached=False)

    DAYCARE_TARGET = DAYCARE_TARGETS.get(selected_age, DAYCARE_TARGETS['1~2세'])
    num_days = len(daily_meals)

    # 식약처 API 기반 영양소 분석 (병렬 조회)
    nutrition_api = wiz.model("nutrition_api")
    month_total = {k: 0.0 for k in DAYCARE_TARGET}
    daily_nutrients = {}  # date → {nutrient: value}
    daily_calories = {}
    daily_menu_entries = {}
    daily_meal_type_totals = {}
    estimated_count = 0
    total_menu_count = 0
    decomposed_count = 0

    try:
        all_tasks = []
        for date_str in sorted(daily_meals.keys()):
            day_kcal = db_daily_kcal.get(date_str)
            for m in daily_meals[date_str]:
                all_tasks.append((date_str, m['meal_type'], m['content'], day_kcal))

        search_results = {}
        if all_tasks:
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = {}
                for i, (date_str, meal_type, content, day_kcal) in enumerate(all_tasks):
                    futures[executor.submit(nutrition_api.analyze_meal_pipeline, content, selected_age)] = i
                for future in futures:
                    idx = futures[future]
                    try:
                        search_results[idx] = future.result()
                    except Exception:
                        search_results[idx] = {'menus': [], 'total': {}, 'found_count': 0, 'total_count': 0}

        for i, (date_str, meal_type, content, day_kcal) in enumerate(all_tasks):
            meal_result = search_results.get(i, {'menus': [], 'total': {}, 'found_count': 0, 'total_count': 0})
            # 추정값 카운트 집계
            for menu in meal_result.get('menus', []):
                total_menu_count += 1
                if menu.get('is_estimated'):
                    estimated_count += 1
                if menu.get('match_type') == 'decomposed':
                    decomposed_count += 1
            scaled = nutrition_api.compute_scaled_nutrients(meal_result, meal_type, selected_age, day_kcal if meal_type == '점심' else None)

            if date_str not in daily_menu_entries:
                daily_menu_entries[date_str] = []
            for menu in meal_result.get('menus', []):
                menu_item = dict(menu)
                menu_item['meal_type'] = meal_type
                daily_menu_entries[date_str].append(menu_item)

            if date_str not in daily_meal_type_totals:
                daily_meal_type_totals[date_str] = {}
            daily_meal_type_totals[date_str][meal_type] = scaled

            if date_str not in daily_nutrients:
                daily_nutrients[date_str] = {k: 0.0 for k in DAYCARE_TARGET}
            for k in DAYCARE_TARGET:
                val = scaled.get(k, 0)
                daily_nutrients[date_str][k] += val
                month_total[k] += val

        # 일별 칼로리 합산
        for date_str, dn in daily_nutrients.items():
            daily_calories[date_str] = round(dn.get('calories', 0))
        # DB kcal 우선 적용
        for date_str, kcal in db_daily_kcal.items():
            daily_calories[date_str] = kcal
    except Exception:
        pass

    # 영양소 충족률 계산
    nutrients = {}
    deficient_nutrients = []

    for key in DAYCARE_TARGET:
        target_per_day = DAYCARE_TARGET[key]['value']
        total_target = target_per_day * num_days
        actual = month_total.get(key, 0)
        avg_daily = round(actual / num_days, 1) if num_days > 0 else 0

        if total_target > 0:
            percent = min(round((actual / total_target) * 100), 100)
        else:
            percent = 0

        status = "양호" if percent >= 80 else "부족"
        display_name = DISPLAY_NAMES[key]

        nutrients[display_name] = {
            'key': key,
            'percent': percent,
            'target': DAYCARE_TARGET[key]['label'],
            'target_value': target_per_day,
            'avg_daily': avg_daily,
            'status': status,
            'unit': DAYCARE_TARGET[key].get('unit', '')
        }

        if percent < 80:
            deficient_nutrients.append({
                'name': display_name,
                'percent': percent,
                'target': DAYCARE_TARGET[key]['label'],
                'avg_daily': avg_daily
            })

    # AI 종합 분석 및 보충 조언
    summary = ""
    daily_evaluations = {}
    warning_counts = {}
    for date_str, totals in daily_nutrients.items():
        evaluation = nutrition_api.evaluate_daycare_nutrition(
            totals,
            daily_menu_entries.get(date_str, []),
            daily_meal_type_totals.get(date_str, {})
        )
        daily_evaluations[date_str] = evaluation
        for warning in evaluation.get('warnings', []):
            key = warning.get('type', 'other')
            if key not in warning_counts:
                warning_counts[key] = {
                    'type': key,
                    'message': warning.get('message', ''),
                    'days': 0,
                }
            warning_counts[key]['days'] += 1

    evaluation = nutrition_api.evaluate_daycare_nutrition(
        {k: (month_total.get(k, 0) / num_days if num_days > 0 else 0) for k in ['calories', 'carbohydrate', 'protein', 'fat', 'sodium']},
        [item for items in daily_menu_entries.values() for item in items],
        {}
    )
    evaluation['warnings'] = sorted(warning_counts.values(), key=lambda x: (-x['days'], x['type']))

    if deficient_nutrients:
        deficient_text = "\n".join([f"- {d['name']}: 달성률 {d['percent']}% (기준: {d['target']}, 일평균: {d['avg_daily']})" for d in deficient_nutrients])
        prompt = f"""{year}년 {mon}월 {selected_age} 어린이집 식단(점심+간식2회) 분석 결과입니다.
등원일수: {num_days}일

아래 영양소가 부족합니다:
{deficient_text}

각 부족 영양소에 대해 보충 조언(advice)과 이모지(emoji)를 제공하고,
전체 종합 평가(summary)를 2-3문장으로 작성해주세요.
JSON 형식: {{"deficient_advice": [{{"name": "영양소명", "emoji": "🍊", "advice": "구체적 보충 조언"}}], "summary": "종합 평가"}}"""

        try:
            gemini = wiz.model("gemini")
            ai_result = gemini.ask_json(prompt, system_instruction="어린이 영양사입니다. JSON만 응답하세요.")
            if isinstance(ai_result, dict):
                for da in ai_result.get('deficient_advice', []):
                    for dn in deficient_nutrients:
                        if dn['name'] == da.get('name'):
                            dn['emoji'] = da.get('emoji', '📊')
                            dn['advice'] = da.get('advice', '')
                summary = ai_result.get('summary', '')
        except Exception:
            pass

        for dn in deficient_nutrients:
            if 'emoji' not in dn:
                dn['emoji'] = '📊'
            if 'advice' not in dn:
                dn['advice'] = f"{dn['name']} 섭취가 부족합니다. 관련 식품을 보충해주세요."
        if not summary:
            names = ", ".join([d['name'] for d in deficient_nutrients])
            summary = f"이번 달 식단에서 {names}의 섭취가 부족합니다. 가정에서 보충 식품을 제공해주세요."
    else:
        summary = f"이번 달 어린이집 식단({num_days}일)의 영양 균형이 전반적으로 양호합니다. 모든 영양소가 기준치의 80% 이상 충족되었습니다."

    result = dict(
        month=month,
        age=selected_age,
        total_days=num_days,
        daily_calories=daily_calories,
        nutrients=nutrients,
        deficient_nutrients=deficient_nutrients,
        summary=summary,
        ages=list(DAYCARE_TARGETS.keys()),
        estimated_count=estimated_count,
        total_menu_count=total_menu_count,
        decomposed_count=decomposed_count,
        evaluation=evaluation,
        daily_evaluations=daily_evaluations
    )

    # 캐시 저장
    try:
        cache_data = dict(result)
        cache_data['cached_at'] = _now_kst().strftime("%Y-%m-%d %H:%M")
        cache_fs.write.json(cache_file, cache_data)
    except Exception:
        pass

    wiz.response.status(200, **result, cached=False)


def get_mapping_review_items():
    role = wiz.session.get("role")
    if role not in ("teacher", "director"):
        wiz.response.status(403, message="권한이 없습니다.")

    limit = int(wiz.request.query("limit", "200"))
    rows = NutritionMapping.select().order_by(NutritionMapping.updated_at.desc()).limit(limit)
    items = []

    for row in rows:
        try:
            nutrients = json.loads(row.nutrients) if row.nutrients else {}
        except Exception:
            nutrients = {}

        match_type = nutrients.get('match_type', '')
        review_needed = bool(nutrients.get('review_needed'))
        is_estimated = bool(nutrients.get('is_estimated'))
        is_decomposed = bool(nutrients.get('is_decomposed'))
        if not (review_needed or is_estimated or is_decomposed or match_type in ('similar', 'representative', 'manual')):
            continue

        items.append({
            'menu_name': row.menu_name,
            'matched_food_name': nutrients.get('matched_food_name', row.food_name or ''),
            'lookup_query': nutrients.get('lookup_query', ''),
            'source': row.source,
            'match_type': match_type,
            'match_reason': nutrients.get('match_reason', ''),
            'review_needed': review_needed,
            'note': nutrients.get('note', ''),
            'is_estimated': is_estimated,
            'is_decomposed': is_decomposed,
            'decomposition_components': nutrients.get('decomposition_components', []),
            'updated_at': row.updated_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(row.updated_at, 'strftime') else str(row.updated_at),
        })

    wiz.response.status(200, items=items)


def save_manual_mapping():
    role = wiz.session.get("role")
    if role not in ("teacher", "director"):
        wiz.response.status(403, message="권한이 없습니다.")

    menu_name = wiz.request.query("menu_name", True).strip()
    search_name = wiz.request.query("search_name", True).strip()
    note = wiz.request.query("note", "수동 확정 매핑").strip()

    fs = wiz.project.fs("data")
    data = fs.read.json("nutrition_manual_mappings.json", default={'mappings': {}})
    if not isinstance(data, dict):
        data = {'mappings': {}}
    mappings = data.get('mappings', {})
    if not isinstance(mappings, dict):
        mappings = {}

    mappings[menu_name] = {
        'search': search_name,
        'note': note
    }
    data['mappings'] = mappings
    fs.write.json("nutrition_manual_mappings.json", data)

    nutrition_api = wiz.model("nutrition_api")
    nutrition_api.clear_cache()
    wiz.response.status(200, saved=True)
