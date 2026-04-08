# 영양분석 통합 파이프라인 리팩토링

- **ID**: 003
- **날짜**: 2026-04-06
- **유형**: 기능 추가

## 작업 요약
식단 영양분석 시 Gemini 일괄 정규화 → 병렬 식약처 API 검색 → Gemini 일괄 fallback 3단계 통합 파이프라인을 구현하여, 한 번의 요청에서 최대한 정확한 영양 데이터를 반환하도록 개선.
AI 추정값에 `is_estimated: true` 플래그를 추가하고 프론트엔드에서 ⚠ 아이콘으로 표시.

## 변경 파일 목록

### Model (nutrition_api.py)
- `src/model/nutrition_api.py`
  - `normalize_food_names()`: 음식명 리스트를 Gemini로 일괄 정규화 (식약처 검색용)
  - `search_batch()`: 정규화된 이름으로 병렬 식약처 검색 (ThreadPoolExecutor)
  - `_ai_fallback_batch()`: 식약처 미검색 항목 일괄 Gemini 추정
  - `_ai_fallback()`: 프롬프트 개선 + `is_estimated: true` 플래그 추가
  - `analyze_meal_pipeline()`: 3단계 통합 파이프라인 (정규화→병렬검색→fallback)
  - `search_meal()`: 기존 메서드에도 `is_estimated` 플래그 전파 추가

### API (page.note.meal.nutrition/api.py)
- `get_dashboard()`: `search_meal` → `analyze_meal_pipeline` 전환, 추정값 카운트 집계, 응답에 `estimated_count`/`total_menu_count` 포함

### API (page.note.today/api.py)
- `recommend_dinner()`: `search_meal` → `analyze_meal_pipeline` 전환

### Frontend (page.note.meal.nutrition)
- `view.ts`: `estimatedCount`, `totalMenuCount` 변수 추가
- `view.pug`: 추정값 안내 배너 (⚠ 아이콘 + 추정값 개수 표시)
- `view.scss`: `.estimate-banner` 스타일 추가
