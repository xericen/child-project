# 알레르기 알림 UI 아이별 그룹핑

- **ID**: 001
- **날짜**: 2026-03-18
- **유형**: 기능 개선

## 작업 요약
같은 아이의 알레르기를 개별 카드에서 한 카드로 통합하여 표시. API 응답을 child_id 기준으로 그룹핑.

## 변경 파일 목록

### App API
- `component.header/api.py`: `get_weekly_allergy()` 결과를 아이별로 그룹핑. 각 아이에 `allergies` 배열과 통합 `matched_foods` 반환.

### App UI
- `component.header/view.pug`: `.allergy-types` 섹션 추가 (알레르기 태그 목록), `.allergy-type` 단일 필드 제거
- `component.header/view.scss`: `.allergy-types`, `.allergy-label`, `.allergy-type-item` 스타일 추가
