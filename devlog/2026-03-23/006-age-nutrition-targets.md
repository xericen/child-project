# 연령별 영양 기준 업데이트

- **ID**: 006
- **날짜**: 2026-03-23
- **유형**: 기능 수정

## 작업 요약
급식 통계 페이지의 영양 기준값을 올바른 연령별 기준으로 수정. 기존 단일 열량 맵(`AGE_CALORIE_MAP`)을 연령대별 열량/단백질/칼슘 기준(`AGE_NUTRITION`)으로 교체하고, AI 분석 프롬프트와 프론트엔드 UI에 반영.

## 변경 파일 목록

### 백엔드 (api.py)
- `src/app/page.note.meal/api.py`: `AGE_CALORIE_MAP` → `AGE_NUTRITION` (1~2세: 900kcal/20g/450mg, 3~5세: 1400kcal/25g/550mg), `get_stats()` 응답에 `age_nutrition` 추가, AI 프롬프트에 연령별 기준 명시

### 프론트엔드
- `src/app/page.note.meal/view.ts`: `ageNutrition` 배열 변수 추가, `loadStats()`에서 `age_nutrition` 데이터 매핑
- `src/app/page.note.meal/view.pug`: 캘린더 섹션 제목을 연령별 기준 태그로 교체 (단일 targetKcal → 연령대별 kcal 표시)
- `src/app/page.note.meal/view.scss`: `.ns-age-standards`, `.ns-age-tag` 스타일 추가
