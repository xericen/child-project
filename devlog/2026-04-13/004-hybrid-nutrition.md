# 식품 DB + 식품군 하이브리드 영양 분석

- **ID**: 004
- **날짜**: 2026-04-13
- **유형**: 기능 추가

## 작업 요약
영양 분석을 순수 룰 기반(식품군 표준값)에서 하이브리드 방식으로 개선. 로컬 식품 DB(nutrition_foods, BASIC_INGREDIENTS)에서 먼저 정확한 영양값을 검색하고, 미발견 시 식품군 표준값으로 fallback. API/AI는 호출하지 않아 결정적 결과 보장.

## 변경 파일 목록

### 수정
- `src/model/nutrition_api.py`:
  - `BASIC_INGREDIENTS` 클래스 속성 추가 (외부 접근 가능)
  - `search_local()` 메서드 추가: 인메모리 캐시 → DB 매핑 캐시 → BASIC_INGREDIENTS → nutrition_foods DB 순서로 검색. API/AI 미호출, (result, source) 튜플 반환.

- `src/app/page.note.today/api.py`:
  - `_ai_analyze_all_meals()` 함수 하이브리드 방식으로 전면 개편
  - `_SERVING_GRAMS` 식품군별 1인1회 배식량(g) 상수 추가
  - 3단계 로직: 로컬 DB 검색 → per 100g 값을 배식량 기준 스케일 → 식품군 표준값 fallback
  - 각 아이템에 `source` 필드로 데이터 출처 표시 ('local_db', 'basic', 'db_cache', 'food_group')
