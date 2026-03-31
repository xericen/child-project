# 식단표 헤더 버튼 레이아웃 변경 — 영양분석을 네비 탭으로

- **ID**: 004
- **날짜**: 2026-03-30
- **유형**: 기능 추가

## 작업 요약
📈영양분석 버튼을 `.header-row` 상단에서 제거하고, 월간/날짜별과 동일한 수준의 네비게이션 탭(`.menu-buttons`)으로 이동. 📊통계 버튼은 상단 유지.

## 변경 파일 목록
### page.note.meal/view.pug
- `.header-row`에서 `button.btn-dashboard` 제거
- `.menu-buttons`에 `button.menu-btn.menu-btn-accent` 추가 (📊영양분석 탭)

### page.note.meal/view.scss
- `.btn-dashboard` 스타일 삭제
- `.menu-btn-accent` 스타일 추가 (border-color: #5b6ef5, bg: #f0f2ff)
