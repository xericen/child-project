# 알레르기 표시 버그 수정 — save/update 시 번호 누락 + 교사/원장 매칭 누락

- **ID**: 001
- **날짜**: 2026-03-30
- **유형**: 버그 수정

## 작업 요약
식단표(page.note.meal)에서 알레르기 빨간 표시가 사라지는 버그를 수정했다. 원인은 3가지:
1. `save_meal()`에서 수동 저장 시 `allergy_numbers`/`dish_allergies` 필드를 추출하지 않아 NULL로 저장됨
2. `update_meal()`에서 수정 시에도 동일하게 알레르기 데이터가 미갱신됨
3. `get_daily()`에서 교사/원장 역할에 대한 알레르기 매칭이 누락되어 학부모만 경고 표시됨

## 변경 파일 목록

### 백엔드 API
- `src/app/page.note.meal/api.py`
  - `save_meal()`: `_extract_allergy_numbers(content)` + `_extract_dish_allergies(content)` 호출 추가, `Meals.create()`에 `allergy_numbers`/`dish_allergies` 필드 포함
  - `update_meal()`: 동일하게 알레르기 번호 재추출 후 `Meals.update()`에 필드 포함
  - `get_daily()`: 교사/원장 역할에서도 서버 내 모든 자녀의 알레르기 번호를 합산하여 매칭하도록 수정 (기존: parent만 처리)
