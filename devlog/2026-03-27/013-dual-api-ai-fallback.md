# 이중 영양 API (국가표준+메뉴젠) + AI fallback

- **ID**: 013
- **날짜**: 2026-03-27
- **유형**: 기능 추가

## 작업 요약
국가표준식품성분 API(FoodNtrCpntDbInfo02)에서 검색 실패 시 메뉴젠 API(FoodNtrCpntDbInfo01)로 2차 검색. 둘 다 실패 시 Gemini AI로 영양소 추정. 복합조리식(돼지고기하이라이스 등) 검색 성공률 향상.

## 변경 파일 목록
- `src/model/nutrition_api.py`:
  - API_BASE_MENUGEN 상수 추가
  - _api_call(): api_base 파라미터 추가
  - search(): 3단계 fallback (국가표준→메뉴젠→AI)
  - _ai_fallback(): Gemini ask_json으로 영양소 추정
