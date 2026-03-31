# 알레르기 대체식품 AI 추천 기능 구현

- **ID**: 011
- **날짜**: 2026-03-16
- **유형**: 기능 추가

## 작업 요약
`page.note.today`에 Gemini AI 기반 알레르기 대체식품 추천 기능 추가. 교사/원장 전용으로 알레르기 아동별 오늘 식단 중 먹을 수 없는 메뉴를 식별하고, 연령별 칼로리 기준에 맞는 대체 메뉴를 추천.

## 변경 파일 목록

### API
- `src/app/page.note.today/api.py`: `get_allergy_substitutes()` 함수 추가 — 아동별 알레르기·연령·칼로리 정보 + allergy_categories DB 대체식품 → Gemini JSON 응답

### Frontend
- `src/app/page.note.today/view.ts`: `allergySubstitutes`, `substituteLoading`, `showSubstitutes` 상태 변수, `loadSubstitutes()` 메서드 추가
- `src/app/page.note.today/view.pug`: 알레르기 주의 섹션 아래 `🔄 대체식품 AI 추천` 버튼 + 결과 카드 (아동별 원래메뉴→대체메뉴+이유)
- `src/app/page.note.today/view.scss`: 대체식품 섹션 스타일 (`.substitute-section`, `.substitute-card`, `.sub-highlight` 등)
