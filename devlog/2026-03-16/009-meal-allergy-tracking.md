# 식단 알레르기 추적 및 경고 표시 시스템

- **ID**: 009
- **날짜**: 2026-03-16
- **유형**: 기능 추가

## 작업 요약
HWP 식단 파일에서 알레르기 번호(①~⑲)를 추출·저장하고, 일일 식단 조회 시 등록된 원아의 알레르기 정보와 매칭하여 주의 경고를 표시하는 시스템 구현.

## 변경 파일 목록

### DB 스키마
- `ALTER TABLE meals ADD COLUMN allergy_numbers TEXT NULL AFTER content` — 알레르기 번호 JSON 저장용

### Model
- `src/model/db/childcheck/meals.py` — `allergy_numbers = pw.TextField(null=True)` 필드 추가

### API (src/app/page.note.meal/api.py)
- `ALLERGY_MAP` 상수 추가 (19종 알레르기 식품 번호→이름 매핑)
- `ALLERGY_TYPE_TO_NUMBERS` 상수 추가 (child_allergies.allergy_type→번호 매핑)
- `_extract_allergy_numbers(content)` 함수 추가 (원형 숫자 ①~⑲, 후행 숫자, 괄호 숫자 추출)
- `_parse_meal_html()` 수정 — 정제 전 원문에서 알레르기 번호 추출
- `parse_hwp_meal()` 수정 — allergy_numbers를 JSON으로 DB 저장
- `get_daily()` 수정 — allergy_alerts 반환 (child_name, allergy_type, matched_foods)
  - 별도 Children 쿼리로 child_name 매핑 (IntegerField 기반 child_id)
  - 기타 알레르기는 ALLERGY_TYPE_TO_NUMBERS 키워드 매칭, 미매칭 시 상세정보 표시

### 프론트엔드
- `view.ts` — `allergyAlerts` 배열 추가, `loadDaily()`에서 경고 데이터 로드
- `view.pug` — 알레르기 경고 섹션 추가 (teacher/director 전용)
- `view.scss` — 알레르기 경고 카드 스타일 추가 (orange 테마)
