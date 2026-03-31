# 알레르기 대체식품 DB 구축 — HWP 첫장 8개 카테고리

- **ID**: 002
- **날짜**: 2026-03-17
- **유형**: 기능 추가

## 작업 요약
HWP 첫 장의 "식품 알레르기 유발 식품 대체 안내" 8개 카테고리(난류, 우유류, 견과류, 대두, 곡류(메밀), 어류 및 갑각류, 고기류, 과채류)를 DB 테이블 `allergy_categories`로 구축. 각 카테고리별 표준 번호 매핑, 주의식품, 대체식품, 설명을 저장. API에서 주의식품→번호 역매핑(`_build_caution_food_map()`)을 활용하여 `기타` 알레르기의 교차반응 기반 경고도 지원.

## 변경 파일 목록
### DB
- `allergy_categories` 테이블 생성 (childcheck DB)
  - 컬럼: id, category_name, allergy_numbers(JSON), caution_foods, substitute_foods, description, created_at
  - 8개 카테고리 데이터 INSERT

### Model
- `src/model/db/childcheck/allergy_categories.py`: 신규 Peewee 모델 생성

### API
- `src/app/page.note.meal/api.py`:
  - `AllergyCategories` 모델 import 추가
  - `_build_caution_food_map()` 함수 추가 (DB 주의식품→번호 역매핑)
  - `get_daily()`: 기타 타입 매핑 시 DB 기반 caution_food_map 참조 추가
  - `get_daily()`: 응답에 `allergy_categories` 데이터 추가 (원장/교사용)
