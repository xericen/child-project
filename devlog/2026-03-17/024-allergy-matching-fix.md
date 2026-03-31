# 알레르기 매칭 로직 보완 (이구름 닭고기, 준짜이 돼지고기)

- **ID**: 024
- **날짜**: 2026-03-17
- **유형**: 버그 수정

## 작업 요약
이구름(닭고기), 준짜이(돼지고기) 알레르기가 식단에 반영되지 않는 문제 수정. header의 `_build_caution_food_map()`에서 괄호 처리 누락으로 '돼지고기(햄'이 키로 등록되어 '돼지고기' 매칭 실패. 괄호→콤마 변환 추가 및 기타 알레르기의 ALLERGY_TYPE_TO_NUMBERS 번호 기반 매칭 폴백 로직 추가.

## 변경 파일 목록
### component.header
- **api.py**: `_build_caution_food_map()`에 `.replace('(', ',').replace(')', ',')` 추가. `get_weekly_allergy()` 기타 알레르기 분기에서 `ALLERGY_TYPE_TO_NUMBERS` 번호 매칭 폴백 추가
