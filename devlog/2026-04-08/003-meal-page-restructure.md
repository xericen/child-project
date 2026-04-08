# 식단표 페이지 구조 개편 (캘린더 직접 표시 + 영양분석 통합)

- **ID**: 003
- **날짜**: 2026-04-08
- **유형**: 리팩토링

## 작업 요약
식단표 페이지(`page.note.meal`)의 구조를 개편. 기존 메뉴/월간/날짜별/통계 4단계 하위 페이지 구조에서, 캘린더를 기본 화면으로 직접 표시하는 간략한 구조로 변경. 영양분석 대시보드를 별도 페이지(`page.note.meal.nutrition`)에서 식단표 페이지 내부로 통합.

## 변경 파일 목록

### 로직 (view.ts)
- `src/app/page.note.meal/view.ts`:
  - `mode` 기본값 'menu' → 'calendar'로 변경
  - `ngOnInit()`에서 `loadMonthly()` 즉시 호출하여 캘린더 직접 표시
  - `goBack()` 로직 변경: calendar 외 모드 → calendar로 복귀
  - `goMonthly()`, `goNutritionDashboard()` 제거
  - `goNutrition()` 메서드 추가: 기존 stats + nutrition dashboard 통합 로드
  - `loadNutritionDashboard()`: fetch()로 `page.note.meal.nutrition` API 호출
  - `getNutrientColor()` 메서드 추가
  - 영양분석 대시보드 상태 변수 추가 (nutritionData, nutritionNutrientList 등)

### UI (view.pug)
- `src/app/page.note.meal/view.pug`:
  - 메뉴 모드 섹션 전체 제거
  - 'monthly' → 'calendar' 모드로 변경, 캘린더 아래에 파일 목록 통합
  - 'stats' → 'nutrition' 모드로 변경, 영양소 달성률 차트/부족 영양소 조언/AI 평가 추가
  - 헤더 버튼: '📊 통계' → '📊 영양분석'

### 스타일 (view.scss)
- `src/app/page.note.meal/view.scss`:
  - 영양분석 대시보드 스타일 추가 (nut-* 클래스 계열)
