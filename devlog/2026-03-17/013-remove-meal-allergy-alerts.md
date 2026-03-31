# 식단표 페이지 알레르기 주의 섹션 완전 제거

- **ID**: 013
- **날짜**: 2026-03-17
- **유형**: 기능 제거

## 작업 요약
page.note.meal (날짜별 식단표)에서 "⚠️ 오늘의 알레르기 주의" 섹션을 교사/원장 모두에서 완전 삭제. 알레르기 체크 기능은 별도 페이지(page.note.allergy)로 분리되어 있으므로 중복 제거.

## 변경 파일 목록

### page.note.meal (src/app/page.note.meal/)
| 파일 | 변경 내용 |
|------|----------|
| view.pug | `.allergy-alert-section` 전체 제거, 개별 식단 카드 `.meal-allergy-info` 제거 |
| view.ts | `allergyAlerts`, `allergyMap`, `ALLERGY_MAP`, `getAllergyNames()` 변수/함수 제거. `loadDaily()`에서 allergy_alerts/allergy_map 수신 코드 제거 |
| api.py | `get_daily()`에서 아동 알레르기 조회·매칭 로직(allergy_alerts, allergy_categories) 100줄+ 제거. 식단 데이터만 반환하도록 단순화 |
