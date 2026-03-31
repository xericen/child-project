# 음식별 알레르기 매핑 및 식단명 표시 개선

- **ID**: 014
- **날짜**: 2026-03-23
- **유형**: 기능 추가 / 버그 수정

## 작업 요약
알레르기 주의 식단에서 재료 키워드(난류, 달걀 등) 대신 실제 음식 이름(미트볼조림, 모닝빵우유 등)이 표시되도록 개선.
기존에는 알레르기 번호가 식단(meal) 단위로만 저장되어 어떤 음식이 어떤 알레르기를 가지는지 구분 불가능했으나,
HWP 원본의 음식별 알레르기 마커(①②③)를 파싱하여 `dish_allergies` 컬럼에 저장하도록 변경.
추가로 분수 패턴(1/2, 1/3 등 서빙 사이즈)이 알레르기 번호로 잘못 추출되던 버그도 수정.

## 변경 파일 목록

### DB 스키마
- `meals` 테이블에 `dish_allergies TEXT NULL` 컬럼 추가
- `src/model/db/childcheck/meals.py`: Peewee 모델에 `dish_allergies` 필드 추가

### 백엔드 API (page.note.meal/api.py)
- `_extract_allergy_numbers()`: 분수 패턴(`\d+/\d+`) 전처리 추가
- `_extract_dish_allergies()`: 신규 함수 — 원본 content에서 음식별 알레르기 번호 dict 추출
- `_clean_meal_content()`: 분수 패턴 전처리 추가
- `_parse_meal_html()`: `dish_allergies` 추출 포함
- `parse_hwp_meal()`: `Meals.create()`에 `dish_allergies` 저장
- `get_parent_stats()`: `dish_allergies` 우선 사용, fallback으로 기존 키워드 매칭 유지. 기타 알레르기에 `other_detail` 표시 (예: "기타(굴, 키위)")

### 헤더 알레르기 (component.header/api.py)
- `get_weekly_allergy()`: `dish_allergies` 수집 및 우선 매칭 사용, fallback으로 기존 키워드 매칭

### 데이터 마이그레이션
- 기존 3월 HWP 데이터 재파싱: 75개 식단에 `dish_allergies` 채움
- 분수 버그로 인한 잘못된 content/allergy_numbers 17건 수정
