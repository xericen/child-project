# 알레르기 알림에 실제 식단명 표시

- **ID**: 012
- **날짜**: 2026-03-23
- **유형**: 기능 개선

## 작업 요약
스케줄러 알레르기 알림 메시지에 기존 알레르기 분류명("난류(계란)") 대신 실제 식단명("달걀채소볶음(난류)")을 포함하도록 개선. AllergyCategories DB의 caution_foods 매핑과 키워드 검색을 활용하여 식단 content에서 해당 음식명을 추출.

## 변경 파일 목록

### 스케줄러
- `src/route/api.scheduler/controller.py`
  - `import re`, `AllergyCategories` 모델 import 추가
  - `KEYWORD_ALIASES` 상수 추가 (돼지→돼지고기, 닭→닭고기 등 유의어)
  - `_build_allergy_food_map()`: AllergyCategories DB에서 알레르기 번호→주의식품 키워드 매핑 생성
  - `_find_dish_names()`: 식단 content에서 알레르기 해당 음식명 추출 (키워드 매칭 + 유의어)
  - `check_allergies()`: `num_to_foods` 맵 생성, `all_content` 수집, `dish_details` 전달
  - `_notify_allergy_matches()`: 부모 알림에 "식단명(알레르기명)" 형태로 표시, 교직원 요약에도 식단명 포함
