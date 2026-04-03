# 영양 분석 7건 수정 (통계UI, 중앙정렬, 연령별구분, 카드불일치, 저녁추천, 로깅, 검증)

- **ID**: 001
- **날짜**: 2026-04-02
- **유형**: 버그 수정

## 작업 요약
FN-20260402-0001~0007까지 7건의 수정을 일괄 수행. 통계 페이지 캘린더만 표시, 영양분석 페이지 중앙정렬, AI평가 연령별 구분, Card1/Card2 칼로리 불일치 이중스케일링 버그 수정, 저녁추천 연령기준 동적표시, 전체 파이프라인 로깅 추가, API 호출 검증 완료.

## 변경 파일 목록

### page.note.meal (통계 페이지)
- `view.pug`: 통계 모드에서 요약카드, 알레르기 섹션, AI 로딩, 영양소 충족률, 보충필요 영양소 섹션 제거. 캘린더만 유지.

### page.note.meal.nutrition (영양분석 페이지)
- `view.scss`: `:host`에 `width: 100%` 추가, `.dashboard-wrap`의 `margin: 12px` → `margin: 12px auto`로 중앙정렬 강화.
- `api.py`: `selected_age = "1~2세"` 하드코딩 → 부모 자녀 나이 기반 동적 결정. 3~5세일 때 `kcal_35` DB 컬럼 사용.

### page.note.today (오늘의 식단)
- `view.ts`: `fixGreenAndScaling()` Stage 2 이중스케일링 제거. Stage 1 필터링 합산(rawTotal)을 Stage 2 consumed로 직접 사용. DAYCARE_TARGET은 childAge 기반 동적 선택.
- `view.pug`: Stage 2 배지 "1-2세 기준" 하드코딩 → `analysis.stage2.age` 기반 동적 텍스트.
- `api.py`: recommend_dinner()에 자녀정보/DB열량선택/끼니별배분/Stage별합산 상세 print 로깅 추가.
