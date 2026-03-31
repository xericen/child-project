# 부모 식단페이지 알레르기 매칭 수정

- **ID**: 001
- **날짜**: 2026-03-27
- **유형**: 버그 수정

## 작업 요약
회원정보에서 알레르기를 수정하면 DB는 반영되지만, 식단표와 매칭되지 않는 문제를 수정. `기타` 알레르기 타입의 `other_detail` 필드가 번호 변환에 반영되지 않던 버그를 scheduler의 레퍼런스 구현과 동일하게 3개 위치에서 수정.

## 변경 파일 목록

### page.note.meal/api.py
- `ALLERGY_TYPE_TO_NUMBERS`: `'쇠고기': [16]` 키 추가 (scheduler와 동일)
- `_get_child_allergy_numbers()`: `기타` 타입일 때 `other_detail`을 `ALLERGY_TYPE_TO_NUMBERS`에서 검색, 콤마/공백/슬래시 분리 후 개별 매칭 로직 추가
- `get_parent_stats()` 내 알레르기 번호 변환: `기타` 타입일 때 `other_detail`에서 번호 변환 로직 추가 (기존에는 키워드 텍스트 매칭만 하고 번호 변환은 누락)

### page.note.today/api.py
- `ALLERGY_TYPE_TO_NUMBERS`: `'쇠고기': [16]` 키 추가
- `get_today_menu()` parent 분기: `기타` + `other_detail` 파싱 → 번호 변환 로직 추가
- `get_today_menu()` teacher/director 분기: 동일 로직 추가
