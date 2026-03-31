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
    selected_age = wiz.request.query("age", "1~2세")
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
            if row.kcal and row.kcal > 0:
                db_daily_kcal[date_str] = row.kcal
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
                    futures[executor.submit(nutrition_api.search_meal, content)] = i
                for future in futures:
                    idx = futures[future]
                    try:
                        search_results[idx] = future.result()
                    except Exception:
                        search_results[idx] = {'menus': [], 'total': {}, 'found_count': 0, 'total_count': 0}

        for i, (date_str, meal_type, content, day_kcal) in enumerate(all_tasks):
            meal_result = search_results.get(i, {'menus': [], 'total': {}, 'found_count': 0, 'total_count': 0})
            scaled = nutrition_api.compute_scaled_nutrients(meal_result, meal_type, selected_age, day_kcal if meal_type == '점심' else None)

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
        ages=list(DAYCARE_TARGETS.keys())
    )

    # 캐시 저장
    try:
        cache_data = dict(result)
        cache_data['cached_at'] = _now_kst().strftime("%Y-%m-%d %H:%M")
        cache_fs.write.json(cache_file, cache_data)
    except Exception:
        pass

    wiz.response.status(200, **result, cached=False)
