# 학부모 페이지 — 교사 대체식 선택 + 연령별 자동분기 반영

- **ID**: 004
- **날짜**: 2026-04-07
- **유형**: 기능 추가

## 작업 요약
학부모 "오늘의 식단"(page.note.today)과 "식단표 날짜별"(page.note.meal daily) 페이지에서 교사의 대체식 선택 결과와 자녀 연령 기반 메뉴 분기를 반영하도록 했다.

## 변경 파일 목록
### page.note.today/api.py
- `MealSubstituteSelections` 모델 로딩 추가
- `_apply_parent_content()` 함수 신규: 교사 선택 반영 + 연령별 분기
- `_get_today_meals()`: meal.id 포함하도록 수정
- `get_today_menu()`: 학부모일 때 자녀 나이 조회 → `_apply_parent_content()` 적용

### page.note.meal/api.py
- `_AGE_MENU_PAIRS`, `_apply_parent_content()` 함수 추가
- `get_daily()`: 학부모일 때 content를 변환하여 반환
