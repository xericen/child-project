# AI 저녁 메뉴 추천 기능 구현

- **ID**: 010
- **날짜**: 2026-03-16
- **유형**: 기능 추가

## 작업 요약
`page.note.today`에 Gemini AI 기반 저녁 메뉴 추천 기능 추가. 부모 전용 버튼으로 오늘 식단을 영양소별 분석 후 가정 저녁 메뉴 2~3개를 추천.

## 변경 파일 목록

### Model
- `src/model/gemini.py`: GeminiHelper 클래스 수정 — `Model = GeminiHelper()` 싱글톤으로 변경, `ask()` 메서드에서 내부 예외 삼킴 제거

### API
- `src/app/page.note.today/api.py`: `_get_today_meals()` 헬퍼 추출, `recommend_dinner()` 함수 추가 — 오늘 식단 → Gemini 영양 분석 프롬프트 → 저녁 추천 텍스트 반환

### Frontend
- `src/app/page.note.today/view.ts`: `dinnerRecommendation`, `dinnerLoading`, `showDinner` 상태 변수, `recommendDinner()` 메서드 추가
- `src/app/page.note.today/view.pug`: 헤더 우측 `🍽️ 저녁추천` 버튼 (부모 전용), 추천 결과 카드 + 로딩 스피너 UI
- `src/app/page.note.today/view.scss`: 저녁 추천 섹션 스타일 (`.dinner-section`, `.dinner-loading`, `.spinner` 등)
