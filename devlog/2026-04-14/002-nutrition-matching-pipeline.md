# 영양 매핑 3단계 파이프라인 및 매칭 메타데이터 추가

- **ID**: 002
- **날짜**: 2026-04-14
- **유형**: 기능 추가

## 작업 요약
기존 nutrition_api 검색 흐름을 표준화 이후 exact/normalized 검색, similar 매칭, representative fallback으로 명시적으로 나누었다.
DB 스키마는 유지한 채 nutrients JSON 내부에 `match_type`, `match_reason`, `lookup_query`, `matched_food_name` 등 검수용 메타데이터를 함께 저장하도록 정리했다.

## 변경 파일 목록

### Model
- `src/model/nutrition_api.py`
  - 유사 매칭/대표값 규칙 로더 추가
  - `_search_resolved_name()`로 실제 조회 단계 분리
  - `_find_similar_rule()`, `_find_representative_rule()`, `_build_representative_result()` 추가
  - `search()`를 exact/normalized → similar → representative → AI fallback 순서로 재구성
  - 반환 결과와 캐시 데이터에 `match_type`, `match_reason`, `lookup_query`, `matched_food_name`, `normalized_by`, `review_needed` 메타데이터 추가
  - DB 캐시 조회 시 row의 `source`, `food_name`, `food_code`를 nutrients JSON에 보완하도록 수정

### Data
- `data/nutrition_matching_rules.json`
  - 크림파스타, 불고기덮밥, 유부장국 등 유사 매칭 규칙 정의
  - 과일, 국, 채소무침, 채소볶음, 김치류 대표값 fallback 규칙 정의