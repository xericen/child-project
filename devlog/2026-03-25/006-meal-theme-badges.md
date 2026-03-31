# 급식 메뉴 7가지 테마 뱃지 구현

- **ID**: 006
- **날짜**: 2026-03-25
- **유형**: 기능 추가

## 작업 요약
식단에 적용된 7가지 테마(차차밥상, 자연밥상, 바다밥상, 고소밥상, 뚝딱밥상, 알록달록밥상, 건강밥상)를 뱃지로 표시하는 기능을 구현했다. DB에 theme 컬럼을 추가하고, HWP 파싱 시 테마를 자동 추출하여 저장하며, 캘린더 및 일별 상세 뷰에 테마 뱃지를 렌더링한다.

## 변경 파일 목록

### DB
- **MySQL meals 테이블**: `theme VARCHAR(50) NULL` 컬럼 추가 (ALTER TABLE)

### Model
- **`model/db/childcheck/meals.py`**: `theme = pw.CharField(max_length=50, null=True)` 필드 추가

### Backend (api.py)
- **`app/page.note.meal/api.py`**:
  - `MEAL_THEMES` 상수 추가 (7가지 테마 이름, 이모지, 키워드)
  - `_extract_theme()` 함수 추가 (텍스트에서 테마 키워드 매칭)
  - `_parse_meal_html()`: 테마 행 감지 로직 추가, 점심 내용에서 테마 추출 fallback, `daily_theme` 딕셔너리 반환
  - `parse_hwp_meal()`: `Meals.create()` 에 `theme=meal_theme` 추가
  - `get_monthly()`: 응답에 `theme` 필드 포함
  - `get_daily()`: 응답에 `theme` 필드 포함

### Frontend
- **`app/page.note.meal/view.ts`**:
  - `MEAL_THEMES` 상수 추가 (이모지, 색상 매핑)
  - `getThemeInfo()`, `getDayTheme()` 헬퍼 메서드 추가
  - `buildCalendar()`에 테마 정보 포함
- **`app/page.note.meal/view.pug`**:
  - 캘린더: `cal-day-cell` + `cal-theme-badge` 뱃지 추가
  - 일별 상세: `day-theme-banner` 배너 추가
- **`app/page.note.meal/view.scss`**:
  - `.cal-day-cell`, `.cal-day-num`, `.cal-theme-badge` 스타일
  - `.day-theme-banner`, `.day-theme-emoji`, `.day-theme-name` 스타일
