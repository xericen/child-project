# 영양 데이터 소스를 로컬 DB 검색으로 전환

- **ID**: 009
- **날짜**: 2026-03-30
- **유형**: 기능 추가

## 작업 요약
기존 식약처 실시간 API 호출을 로컬 nutrition_foods DB(55만건) 우선 검색으로 전환. nutrition_api.py의 검색 파이프라인에 3.5단계(로컬 DB LIKE 검색) 삽입. API는 fallback으로 유지.

## 변경 파일 목록
### src/model/db/childcheck/nutrition_foods.py (신규)
- Peewee ORM 모델 생성 (nutrition_foods 테이블 매핑)

### src/model/nutrition_api.py
- `_NutritionFoods` 필드 추가 + `_get_foods_model()` 지연 로딩
- `_db_search(menu_name)` 신규 — 정확매칭 → LIKE 검색 → 원재료명 추출 후 재검색 3단계
- `_foods_row_to_nutrient(row)` — DB 행 → 영양소 dict 변환
- `_score_foods_match(query, row)` — 로컬 DB 후보 적합도 채점 (가정식/급식 우선)
- `search()` 메서드에 3.5단계 로컬 DB 검색 삽입 (인메모리→DB매핑→BASIC→**로컬DB**→API→AI)
