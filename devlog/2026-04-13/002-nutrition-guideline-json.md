# 가이드라인 데이터 JSON 외부화

- **ID**: 002
- **날짜**: 2026-04-13
- **유형**: 리팩토링

## 작업 요약
식약처 영유아 단체급식 가이드라인 핵심 데이터(식품군별 표준 영양값, 연령별 제공 횟수, 대표식단 영양성분, 1인1회 배식량 등)를 `data/nutrition_guideline.json`으로 외부화하고, api.py에서 JSON 로드 + 인라인 fallback 방식으로 참조하도록 변경.

## 변경 파일 목록

### 신규
- `data/nutrition_guideline.json`: 가이드라인 전체 데이터 (food_group_standards, meal_serving_counts, daily_serving_counts, daily_energy, daycare_targets, representative_meals, serving_weights)

### 수정
- `src/app/page.note.today/api.py`:
  - `_load_guideline()` 함수 추가 (프로젝트 data 폴더에서 JSON 로드)
  - `FOOD_GROUP_STANDARDS`, `MEAL_SERVING_COUNTS` 상수를 JSON 우선 로드 + 인라인 fallback으로 변경
  - 고아 닫는 브래킷 정리
