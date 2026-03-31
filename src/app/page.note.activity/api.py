# pyright: reportUndefinedVariable=false, reportMissingImports=false
import datetime
import json

Meals = wiz.model("db/childcheck/meals")

def _get_server_id():
    server_id = wiz.session.get("server_id") or wiz.session.get("join_server_id")
    if not server_id:
        wiz.response.status(401, message="서버 정보가 없습니다.")
    return int(server_id)

def get_weekly_foods():
    role = wiz.session.get("role")
    if not role:
        wiz.response.status(401, message="로그인이 필요합니다.")

    server_id = _get_server_id()
    today = datetime.date.today()
    weekday = today.weekday()
    monday = today - datetime.timedelta(days=weekday)
    friday = monday + datetime.timedelta(days=4)

    menu_text = ""
    try:
        rows = Meals.select().where(
            (Meals.server_id == server_id) & (Meals.meal_date >= monday) & (Meals.meal_date <= friday)
        ).order_by(Meals.meal_date, Meals.id)
        for row in rows:
            menu_text += f"- {row.meal_date} {row.meal_type}: {row.content}\n"
    except Exception:
        pass

    if not menu_text:
        wiz.response.status(200, foods=[])

    system_instruction = """당신은 어린이 영양 교육 전문가입니다. 
1주일 어린이집 식단에서 아이들이 먹은 과일, 채소, 곡물 중 재미있는 활동으로 연결할 수 있는 식재료 8개를 골라주세요.
반드시 아래 JSON 배열 형식으로만 답변하세요. 설명 없이 JSON만 출력하세요.
[{"name": "딸기", "emoji": "🍓"}, {"name": "고구마", "emoji": "🍠"}]
emoji는 해당 음식에 가장 어울리는 이모지를 사용하세요.
아이들이 친숙하고 흥미를 느낄 수 있는 식재료를 우선 선택하세요."""

    prompt = f"""이번 주 어린이집 식단입니다:

{menu_text}

이 식단에서 아이들이 좋아할 만한 과일, 채소, 곡물 등 식재료 8개를 골라 JSON 배열로 답변해주세요."""

    try:
        gemini = wiz.model("gemini")
        result = gemini.ask_json(prompt, system_instruction=system_instruction)
    except Exception:
        wiz.response.status(200, foods=[])
    if isinstance(result, list):
        wiz.response.status(200, foods=result[:8])
    wiz.response.status(200, foods=[])

def recommend_activity():
    role = wiz.session.get("role")
    if not role:
        wiz.response.status(401, message="로그인이 필요합니다.")

    food_name = wiz.request.query("food", True)

    system_instruction = """당신은 유아 교육 전문가입니다. 음식 재료를 활용한 가정 활동을 추천합니다.
반드시 한국어로 답변하세요. 반드시 아래 JSON 배열 형식으로만 답변하세요. 설명 없이 JSON만 출력하세요.
[{"title": "활동 제목", "type": "요리", "description": "2~3줄 활동 설명", "icon": "🧑‍🍳"}]
type은 반드시 "요리", "체험", "놀이" 중 하나입니다.
icon은 type에 맞는 이모지를 사용하세요: 요리=🧑‍🍳, 체험=🌿, 놀이=🎨
3개의 활동을 추천해주세요. 각 type이 하나씩 포함되도록 해주세요."""

    prompt = f"""아이가 이번 주 어린이집에서 "{food_name}"을(를) 맛있게 먹었습니다.

"{food_name}"을(를) 활용하여 가정에서 부모와 아이가 함께 할 수 있는 활동 3개를 추천해주세요.
- 요리 활동: 집에서 간단히 만들 수 있는 요리
- 체험 활동: 농장 방문, 마트 체험 등
- 놀이 활동: 미술, 과학 실험 등 창의 활동"""

    try:
        gemini = wiz.model("gemini")
        result = gemini.ask_json(prompt, system_instruction=system_instruction)
    except Exception:
        wiz.response.status(200, activities=[])
    if isinstance(result, list):
        wiz.response.status(200, activities=result)
    wiz.response.status(200, activities=[])
