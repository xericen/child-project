# 활동 추천 페이지 생성 및 AI 활동 추천 연동

- **ID**: 012
- **날짜**: 2026-03-16
- **유형**: 기능 추가

## 작업 요약
부모 전용 `page.note.activity` 페이지 생성. Gemini AI로 1주일 식단에서 아이 친화적 식재료 8개를 추출하고, 선택한 식재료를 활용한 가정 활동(요리/체험/놀이) 3개를 추천하는 기능 구현.

## 변경 파일 목록

### Page 생성
- `src/app/page.note.activity/app.json`: 신규 — mode=page, viewuri=/note/activity, controller=base
- `src/app/page.note.activity/api.py`: 신규 — `get_weekly_foods()` (주간 식단→Gemini→8개 식재료 JSON), `recommend_activity()` (선택 식재료→Gemini→3개 활동 JSON)
- `src/app/page.note.activity/view.ts`: 신규 — foods/selectedFood/activities 상태, loadFoods/selectFood 메서드
- `src/app/page.note.activity/view.pug`: 신규 — 4x2 음식 카드 그리드 + 활동 추천 카드 리스트 (유형별 배지)
- `src/app/page.note.activity/view.scss`: 신규 — food-grid/activity-card/badge 스타일

### 기존 파일 수정
- `src/app/page.note/view.ts`: 부모 메뉴에 `{ icon: '🎨', label: '활동 추천', path: '/note/activity' }` 버튼 추가
