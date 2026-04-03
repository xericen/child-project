# 식단 통계/영양분석 4건 수정

- **ID**: 001
- **날짜**: 2026-04-01
- **유형**: 버그 수정

## 작업 요약
1. 3~5세 통계 열량 캘린더 버그: selectAge()에서 서버 재호출하여 kcal_35 데이터 반영
2. 영양분석 페이지 열량 캘린더/추이 제거 (통계에 이미 존재하므로 중복)
3. 오늘의 식단 로딩 텍스트 색상 검정으로 수정 (p태그에 !important 적용)
4. Stage 1 오늘 섭취 영양소를 DB 총열량에 맞춰 스케일링

## 변경 파일 목록

### 프론트엔드
- `src/app/page.note.meal/view.ts`: loadStats()에 age 파라미터 전달, selectAge()에서 loadStats() 재호출
- `src/app/page.note.meal.nutrition/view.ts`: 열량 캘린더/차트 관련 변수·메서드 제거
- `src/app/page.note.meal.nutrition/view.pug`: 일별 열량 추이, 열량 캘린더 UI 제거, 요약카드 간소화
- `src/app/page.note.today/view.pug`: 로딩 텍스트 p태그에 color:#222 !important 적용

### 백엔드
- `src/app/page.note.today/api.py`: Stage 1에도 DB 열량 ratio를 적용하여 스케일링
