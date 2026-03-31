# 영양분석 파이프라인 개선 — DB 매핑 캐시 + AI 최적 후보 선택

- **ID**: 002
- **날짜**: 2026-03-30
- **유형**: 기능 추가

## 작업 요약
`nutrition_api.py`의 검색 파이프라인을 6단계로 확장: 인메모리 캐시 → **DB 매핑 캐시** → 기본재료 → 국가표준 API → 메뉴젠 API → **AI 매칭** → AI fallback. 영구 DB 매핑 테이블(`nutrition_mapping`)을 추가하여 API 호출 절감 및 검색 정확도 향상.

## 변경 파일 목록

### 신규 생성
- `src/model/db/childcheck/nutrition_mapping.py` — Peewee ORM 모델 (menu_name → food_code, food_name, source, nutrients JSON)
- MySQL `childcheck.nutrition_mapping` 테이블 생성

### 수정
- `src/model/nutrition_api.py`
  - `__init__`: `_NutritionMapping` 필드 추가 (지연 로딩)
  - `_get_mapping_model()`: DB 모델 지연 로딩
  - `_db_mapping_get()`: DB 매핑 캐시 조회
  - `_db_mapping_save()`: DB 매핑 캐시 upsert 저장
  - `_extract_base_ingredient()`: 조리법 키워드 제거 (나물무침, 볶음밥, 절임, 장아찌, 비빔 등 21개 접미사)
  - `_ai_select_best()`: Gemini AI로 식약처 API 후보 중 최적 항목 선택
  - `search()`: 6단계 파이프라인으로 확장 — DB 매핑 우선 조회, 원재료명 추출 재검색, AI 후보 선택, 검색 결과 DB 영구 저장
