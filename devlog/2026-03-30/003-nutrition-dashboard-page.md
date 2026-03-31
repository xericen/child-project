# 급식 영양분석 대시보드 UI 신규 페이지 개발

- **ID**: 003
- **날짜**: 2026-03-30
- **유형**: 기능 추가

## 작업 요약
`page.note.meal.nutrition` 대시보드 페이지를 신규 생성. CSS-only 차트(영양소 가로 바, 일별 열량 세로 막대, 열량 캘린더)와 AI 종합 평가 기반의 영양분석 대시보드 구현. 기존 meal 페이지에 영양분석 이동 버튼 추가.

## 변경 파일 목록

### 신규 생성
- `src/app/page.note.meal.nutrition/app.json` — 페이지 메타데이터 (viewuri: `/note/meal/nutrition`, layout: layout.navbar, controller: base)
- `src/app/page.note.meal.nutrition/api.py` — 대시보드 API (`get_role`, `get_dashboard`). 월간 영양소 충족률, 일별 열량 추이, AI 보충 조언 데이터 집계. 캐시 적용.
- `src/app/page.note.meal.nutrition/view.ts` — 대시보드 컴포넌트. 월 네비게이션, 연령 선택, CSS 차트 데이터 가공.
- `src/app/page.note.meal.nutrition/view.pug` — 대시보드 UI: 요약 카드 4개 + AI 종합 평가 + 영양소 달성률 바 차트 + 일별 열량 막대 차트 + 열량 캘린더 + 부족 영양소 보충 조언
- `src/app/page.note.meal.nutrition/view.scss` — 모바일 우선 카드 디자인 (#eef0fb 배경, 400px 카드, 보라 계열 강조, CSS-only 차트 스타일)

### 수정
- `src/app/page.note.meal/view.pug` — 📈 영양분석 버튼 추가 (교사/원장만 노출)
- `src/app/page.note.meal/view.ts` — `goNutritionDashboard()` 메서드 추가
- `src/app/page.note.meal/view.scss` — `.btn-dashboard` 스타일 추가
