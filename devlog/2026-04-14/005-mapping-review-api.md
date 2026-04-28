# 수동 매핑 및 검수 API 추가

- **ID**: 005
- **날짜**: 2026-04-14
- **유형**: 기능 추가

## 작업 요약
저신뢰 매칭과 대표값, 분해 결과를 운영자가 검수할 수 있도록 검수 목록 API를 추가했다.
수동 확정 매핑을 파일로 저장하고 이후 자동 분석에서 우선 사용하도록 수동 매핑 저장 로직과 데이터 파일을 추가했다.

## 변경 파일 목록

### Model
- `src/model/nutrition_api.py`
  - `nutrition_manual_mappings.json` 로드 및 수동 매핑 우선 적용 로직 추가

### API
- `src/app/page.note.meal.nutrition/api.py`
  - `get_mapping_review_items()` 추가: similar / representative / manual / estimated / decomposed 결과 검수 목록 제공
  - `save_manual_mapping()` 추가: 수동 확정 매핑 저장 후 캐시 초기화

### Data
- `data/nutrition_manual_mappings.json`
  - 수동 확정 매핑 저장소 초기 파일 추가