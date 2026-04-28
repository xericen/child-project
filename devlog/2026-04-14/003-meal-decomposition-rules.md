# 복합 메뉴 분해 계산 규칙 및 캐시 연동

- **ID**: 003
- **날짜**: 2026-04-14
- **유형**: 기능 추가

## 작업 요약
카레라이스, 비빔밥, 김치볶음밥, 불고기덮밥 같은 복합 메뉴를 여러 구성 항목으로 분해해 합산하는 로직을 추가했다.
분해 결과는 일반 매핑 결과와 같은 캐시 흐름을 타도록 저장하고, 응답 메뉴 항목에도 분해 구성 정보를 함께 내려 후속 검수와 재사용이 가능하게 했다.

## 변경 파일 목록

### Model
- `src/model/nutrition_api.py`
  - 복합 메뉴 분해 규칙 로더 추가
  - `_find_decomposition_rule()`, `_build_decomposed_result()` 구현
  - `search()`에 복합 메뉴 분해 선처리 추가
  - `analyze_meal_pipeline()`와 `search_meal()` 응답에 `decomposition_components` 메타데이터 추가

### Data
- `data/nutrition_decomposition_rules.json`
  - 카레라이스, 비빔밥, 김치볶음밥, 불고기덮밥 분해 규칙 정의