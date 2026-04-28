# 식단명 룰 기반 표준화 사전 구축

- **ID**: 001
- **날짜**: 2026-04-14
- **유형**: 기능 추가

## 작업 요약
영양분석 파이프라인의 Gemini 정규화 이전 단계에 결정적 룰 기반 표준화 계층을 추가했다.
어린이집 현장 표현을 식약처/영양 DB 검색용 명칭으로 바꾸는 사전을 data 파일로 분리하고, 애매한 메뉴는 검토 필요 플래그와 메모를 함께 남길 수 있게 정리했다.

## 변경 파일 목록

### Model
- `src/model/nutrition_api.py`
  - `nutrition_normalization_rules.json`을 읽는 로더 추가
  - exact 치환, 단어 치환, 공백 보정, 검토 필요 규칙을 적용하는 `_rule_based_normalize()` 구현
  - `search()`, `search_local()`, `normalize_food_names()`가 룰 기반 표준화를 먼저 통과하도록 변경
  - 외부 재사용용 `standardize_food_name()` 메서드 추가

### Data
- `data/nutrition_normalization_rules.json`
  - 소고기무국→쇠고기 무국, 닭볶음탕→닭도리탕, 잡곡밥→혼합곡밥 등 빈출 표준화 사전 추가
  - 야채볶음, 야채무침, 과일, 국 같은 애매어를 검토 필요 항목으로 분리
  - 공백 보정 suffix와 예외 단어 목록 정의