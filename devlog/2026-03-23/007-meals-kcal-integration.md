# meals DB 열량(kcal) 연동 및 통계 개선

- **ID**: 007
- **날짜**: 2026-03-23
- **유형**: 기능 추가

## 작업 요약
meals 테이블에 kcal 컬럼을 추가하고, HWP 식단표 파싱 시 열량 행(열량/단백질)을 자동 추출하여 DB에 저장. 통계 페이지 캘린더의 열량 데이터를 AI 추정에서 DB 실제 데이터로 변경. 연령대별(1~2세/3~5세) 비교 기준 선택 기능 추가.

## 변경 파일 목록

### DB 스키마
- `src/model/db/childcheck/meals.py`: `kcal` IntegerField 추가 (nullable)
- MySQL: `ALTER TABLE meals ADD COLUMN kcal INT NULL`

### 백엔드 (api.py)
- `src/app/page.note.meal/api.py`:
  - `_parse_meal_html()`: 열량/단백질 행 파싱 추가, 4-tuple 반환 (year, month, meals, daily_kcal)
  - `parse_hwp_meal()`: 점심 행에 daily_kcal 저장
  - `save_meal()`: kcal 파라미터 수신/저장
  - `update_meal()`: kcal 파라미터 수신/수정
  - `get_stats()`: daily_calories 맵 DB에서 직접 집계 반환
  - `get_ai_analysis()`: daily_calories 제거, 영양소 분석 전용으로 변경, 실제 열량 정보를 프롬프트에 포함

### 프론트엔드
- `src/app/page.note.meal/view.ts`: 
  - 캘린더를 get_stats() 응답의 daily_calories로 즉시 빌드 (AI 대기 불필요)
  - 연령대 선택(selectAge) 메서드 추가
  - 어린이집 3끼 = 1일 권장량 50% 기준으로 충족/부족 판정
- `src/app/page.note.meal/view.pug`: 연령대 선택 버튼 UI 추가
- `src/app/page.note.meal/view.scss`: `.ns-age-selector`, `.ns-age-btn` 스타일 추가

### 데이터 마이그레이션
- 기존 2026-03 HWP 데이터에서 열량 추출하여 25일치 meals.kcal 업데이트 완료
