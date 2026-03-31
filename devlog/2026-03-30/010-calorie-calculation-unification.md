# 칼로리 계산 통일 + 연령별 1인분 중량 테이블

- **ID**: 010
- **날짜**: 2026-03-30
- **유형**: 리팩토링

## 작업 요약
3곳(get_stats, get_ai_analysis, get_dashboard)에 분산된 DAYCARE_TARGETS, 칼로리 계산 로직을 nutrition_api.py로 통일. 끼니별 비율(오전간식 10%, 점심 35%, 오후간식 10%)과 연령별 1인분 중량 테이블 추가. DAYCARE_TARGETS 값 재조정(1~2세 420→500kcal, 3~5세 640→700kcal).

## 변경 파일 목록
### src/model/nutrition_api.py
- `DAILY_ENERGY` 상수 추가: 1~2세(1000kcal), 3~5세(1400kcal)
- `MEAL_RATIOS` 상수 추가: 오전간식(10%), 점심(35%), 오후간식(10%)
- `DAYCARE_TARGETS` 상수 추가: 6개 영양소 + unit (단일 소스)
- `DISPLAY_NAMES` 상수 추가
- `SERVING_WEIGHTS` 상수 추가: 연령별 × 카테고리별 1인분 중량(g)
- NutritionAPI 클래스에 상수를 클래스 속성으로 참조
- `get_meal_expected_kcal()` 메서드 추가: 끼니별 예상 칼로리 계산
- `compute_scaled_nutrients()` 메서드 추가: 통합 스케일링 (DB kcal 또는 끼니별 예상)

### page.note.meal/api.py
- `AGE_NUTRITION`, `DEFAULT_TARGET_KCAL` 인라인 상수 제거 → shared 참조
- `get_stats()`: selected_age 파라미터 추가, compute_scaled_nutrients 사용, DB kcal 우선 병합 순서 수정
- `get_ai_analysis()`: 인라인 DAYCARE_TARGETS 제거 → shared 참조, compute_scaled_nutrients 사용

### page.note.meal.nutrition/api.py
- 인라인 DAYCARE_TARGETS, DISPLAY_NAMES 제거 → nutrition_api 인스턴스 통해 참조
- compute_scaled_nutrients 통합 스케일링 사용
