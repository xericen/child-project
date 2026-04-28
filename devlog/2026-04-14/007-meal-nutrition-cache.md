# MealNutritionCache 구현 — 영양 분석 캐시 시스템

- **ID**: 007
- **날짜**: 2026-04-14
- **유형**: 기능 추가

## 작업 요약
`MealNutritionCache` DB 테이블이 존재하지만 코드에서 사용되지 않던 것을 활성화하여, `_recommend_dinner_impl()`에서 매번 `_ai_analyze_all_meals()`를 재실행하는 비효율을 해소. 캐시 히트 시 영양 분석을 건너뛰어 저녁 추천 속도를 크게 개선.

## 변경 파일 목록

### page.note.today/api.py
- `_get_nutrition_cache()`: 캐시 조회 함수 추가 (server_id + meal_date + age_group 키)
- `_save_nutrition_cache()`: 캐시 저장 함수 추가 (upsert 방식)
- `_invalidate_nutrition_cache()`: 캐시 무효화 함수 추가
- `_recommend_dinner_impl()`: 캐시 우선 조회 → 미스 시 분석 후 캐시 저장 로직 적용

### page.note.meal/api.py
- `MealNutritionCache` 모델 import 추가
- `_invalidate_nutrition_cache()` 헬퍼 함수 추가
- `save_meal()`: 식단 저장 후 해당 날짜 캐시 무효화
- `update_meal()`: 식단 수정 시 meal_date 조회 후 캐시 무효화
- `delete_meal()`: 식단 삭제 시 meal_date 조회 후 캐시 무효화
- `parse_hwp_meal()`: HWP 업로드 시 해당 서버 전체 캐시 무효화
