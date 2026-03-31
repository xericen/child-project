# 식단 검색 + 알레르기 매칭 빨간색 표시 + 식단 통계

- **ID**: 007
- **날짜**: 2026-03-20
- **유형**: 기능 추가

## 작업 요약
식단표 페이지에 3가지 기능을 추가: (1) 메뉴명/날짜 검색, (2) 학부모 자녀 알레르기와 겹치는 메뉴 빨간색 강조, (3) 월별 식단 통계 (유형별 현황, 자주 나온 메뉴 TOP 15)

## 변경 파일 목록

### page.note.meal/api.py
- `_get_child_allergy_numbers()` 헬퍼 함수 추가: 학부모 자녀의 알레르기 번호 집합 반환
- `get_daily()` 수정: 학부모인 경우 자녀 알레르기와 식단 allergy_numbers 교차 비교, `allergy_match`/`matched_allergens` 필드 반환
- `search_meals()` 신규: keyword로 content LIKE 또는 meal_date 매칭, 최대 50건 반환
- `get_stats()` 신규: 월별 식단 유형별 횟수, 등록일수, 자주 나온 메뉴 TOP 15 집계

### page.note.meal/view.ts
- `searchQuery`, `searchResults`, `searchDone` 변수 추가
- `statsData` 변수 추가 (meal_type_list 포함)
- `goSearch()`, `searchMeals()`, `onSearchResultClick()` 메서드
- `goStats()`, `loadStats()`, `statsPrevMonth()`, `statsNextMonth()` 메서드

### page.note.meal/view.pug
- 메뉴 모드: 검색 🔍, 통계 📊 버튼 추가
- 검색 모드: 검색 입력창 + 결과 리스트 (클릭 시 해당 날짜 daily 모드)
- 통계 모드: 요약 카드(등록일/총 식단) + 유형별 바 차트 + 메뉴 빈도 순위
- 날짜별 모드: `.allergy-danger` 클래스 + "⚠️ 알레르기 주의" 경고 메시지

### page.note.meal/view.scss
- `.meal-card.allergy-danger`: 빨간 테두리 + 연분홍 배경
- `.meal-allergy-warning`: 빨간색 경고 텍스트
- 검색 관련 스타일 (`.search-input-row`, `.search-result-item` 등)
- 통계 관련 스타일 (`.stats-summary`, `.stats-bar`, `.stats-menu-item` 등)
