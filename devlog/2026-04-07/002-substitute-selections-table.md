# 대체식 선택 DB 테이블 및 Model 생성

- **ID**: 002
- **날짜**: 2026-04-07
- **유형**: 기능 추가

## 작업 요약
교사/원장이 날짜별로 대체식(green 마커) 선택 여부를 저장할 수 있도록 `meal_substitute_selections` 테이블과 Peewee Model을 생성했다.

## 변경 파일 목록
### DB
- `meal_substitute_selections` 테이블 생성 (childcheck DB)
  - meal_id, original_item, substitute_item, is_selected, selected_by
  - UNIQUE KEY: (meal_id, original_item)

### Model
- `src/model/db/childcheck/meal_substitute_selections.py` (신규)
  - Peewee Model 정의 (base = orm.base("childcheck"))
