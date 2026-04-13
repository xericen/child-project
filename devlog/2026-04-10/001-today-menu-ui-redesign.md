# 오늘의 식단 페이지 UI 목업 기준 전면 리디자인

- **ID**: 001
- **날짜**: 2026-04-10
- **유형**: 기능 추가

## 작업 요약
사용자 제공 HTML 목업 기준으로 `page.note.today`의 view.scss, view.pug를 전면 재작성. 블루 테마(#5b6ef5, #3a4de4, #eef0fb) 유지하며 목업의 레이아웃·사이즈·스타일을 정확히 반영.

## 변경 파일 목록

### SCSS (view.scss 전면 재작성)
- font-size: rem 단위 → px 단위(10~16px)로 통일, font-weight 500 기본
- border: 1~1.5px → 0.5px로 통일
- card: 공통 스타일(.meal-card, .nutrient-card, .recommend-card) 통합 — 흰색 bg, 0.5px border, 16px radius/padding
- dot: 8px → 6px
- dot-ind: 6px 기본 / active 16px pill (border-radius 3px)
- progress bar: 6px → 4px
- nav 버튼: .nav-btn 단일 → .next-btn(블루 pill) + .prev-btn(흰색 pill) 분리
- 상태 뱃지: .nb-status 텍스트 → .status-badge pill 뱃지 (.badge-good/.badge-warn/.badge-over)
- nutrient-box: 흰색+border → 연파랑 배경(#f0f2fb) 무border
- total-bar: gradient 제거 → 단색 #eef0fb
- .spacer 추가 (페이지 3 nav 오른쪽 정렬용)

### PUG (view.pug 전면 재작성)
- 분석 전 뷰: div → .meal-section 래퍼 추가 (각 끼니별)
- nav 버튼: .next-btn/.prev-btn에 SVG 화살표 인라인 아이콘 추가
- 영양소 상태: span.nb-status → span.status-badge.badge-warn/over/good
- .total-bar, .page-nav, .ingredient-section을 각 카드 내부로 이동
- 페이지 3: .spacer div 추가 (next 버튼 없음)
