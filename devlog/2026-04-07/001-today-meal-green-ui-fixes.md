# 오늘의 식단 green 마커/저녁추천 계산/로깅/UI 수정

- **ID**: 001
- **날짜**: 2026-04-07
- **유형**: 버그 수정 + 기능 개선

## 작업 요약
오늘의 식단 페이지 green 마커 표시 통일, 저녁 추천 시 대체메뉴 제외, 음식별 상세 콘솔 로깅, 백김치/배추김치 분리 표시, 캘린더 overflow·영양분석 버튼·타이틀 정렬 UI 수정.

## 변경 파일 목록

### page.note.today/api.py
- `get_today_menu()`: 학부모용 `_adapt_content_for_age()` 호출 제거 → raw content(green 마커 포함)를 식단표/월간/날짜별과 동일하게 전달
- `_recommend_dinner_impl()`: `_adapt_content_for_age()`로 전처리 후 파이프라인에 전달하여 해당 연령 아닌 메뉴 제거
- 음식별 상세 로깅 추가: 매칭명, 소스, 서빙사이즈, 칼로리, ratio, DB보정 후 칼로리

### page.note.today/view.ts
- `formatMealContent()`: 연령별 연결 메뉴(백김치배추김치) 분리 + 줄바꿈 표시, `\n` → `<br>` 변환 추가

### page.note.meal/view.ts
- `formatMealContent()`: 동일한 연결 메뉴 분리 로직 추가

### page.note.meal/view.scss
- `.menu-btn-accent`: 강조 스타일 제거 (다른 버튼과 동일하게)
- `.ns-cal-day`: overflow:hidden, justify-content:center, min-width:0 추가로 셀 넘침 방지
- `.ns-cal-kcal`: white-space:nowrap, overflow:hidden, text-overflow:ellipsis 추가

### page.note.meal.nutrition/view.scss
- `.dashboard-wrap`: margin:auto 명시로 중앙 정렬 보장
