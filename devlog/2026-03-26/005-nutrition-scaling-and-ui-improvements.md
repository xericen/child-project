# 영양소 고정 수치 계산 + UI 개선 일괄

- **ID**: 005
- **날짜**: 2026-03-26
- **유형**: 기능 추가

## 작업 요약
nutrition_api에 대체제({{green}}) 제외 및 스케일링 함수 추가. 저녁추천/통계의 영양소 계산을 AI→서버 코드로 전환(고정 수치). 1-2세 기준 통일. 오늘의 식단 알레르기 경고 추가. 부모 메뉴에서 아이정보 수정 삭제. 프로필 전화번호 표시 수정.

## 변경 파일 목록

### Model
- `src/model/nutrition_api.py`: search_meal()에서 {{green:}} 라인 제외, scale_to_target() 함수 추가, GREEN_PATTERN 컴파일

### 오늘의 식단 (page.note.today)
- `api.py`: recommend_dinner() 전면 개편 (Stage1/2 서버 계산, Stage3만 AI), get_today_menu()에 부모 알레르기 매칭 추가, _get_today_meals()에 kcal 필드 포함
- `view.ts`: allergyWarnings 상태 추가, hasAllergyWarning/getAllergyText 메서드 추가
- `view.pug`: 알레르기 경고 UI (.allergy-danger, .allergy-warn), stage-badge 라벨 추가
- `view.scss`: .allergy-danger, .allergy-warn, .stage-badge 스타일 추가

### 식단 통계 (page.note.meal)
- `api.py`: AGE_NUTRITION에서 3-5세 제거, DEFAULT_TARGET_KCAL=420, get_ai_analysis() 전면 개편 (서버 기반 달성률 계산, AI는 advice만)

### 노트 메뉴 (page.note)
- `view.ts`: buildMenu()에서 '아이 정보 수정' 메뉴 항목 제거

### 프로필 (page.note.profile)
- `view.scss`: .detail-value에서 white-space:nowrap/overflow:hidden/text-overflow:ellipsis 제거 → word-break:break-all로 변경
