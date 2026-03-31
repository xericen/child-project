# 오늘의 식단 페이지(page.note.today)에 알레르기 경고 추가

- **ID**: 003
- **날짜**: 2026-03-17
- **유형**: 기능 추가

## 작업 요약
`page.note.today`에 `page.note.meal`과 동일한 알레르기 경고 시스템 추가. 각 식단 카드(오전간식/점심/오후간식)에 알레르기 번호 표시, 하단에 원장/교사 전용 알레르기 주의 아동 섹션 추가. DB 기반 주의식품 매핑(`_build_caution_food_map`) 및 기타 알레르기 키워드 검색 로직 모두 포함.

## 변경 파일 목록
### API
- `src/app/page.note.today/api.py`: 전면 재작성
  - AllergyCategories, Children, ChildAllergies 모델 추가
  - ALLERGY_MAP, ALLERGY_TYPE_TO_NUMBERS 매핑 추가
  - `_build_caution_food_map()` 함수 추가
  - `get_today_menu()`: 알레르기 번호, 경고 아동 목록, 매핑 정보 반환 추가

### Frontend
- `src/app/page.note.today/view.ts`: ALLERGY_MAP, allergyAlerts, mealAllergy, getAllergyNames 추가
- `src/app/page.note.today/view.pug`: 식단 카드에 🔸 알레르기 표시 + ⚠️ 알레르기 주의 아동 섹션 추가
- `src/app/page.note.today/view.scss`: .meal-allergy-info, .allergy-alert-section 스타일 추가
