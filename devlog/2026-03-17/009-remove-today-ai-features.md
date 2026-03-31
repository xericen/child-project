# 원장/교사 오늘의 식단 — AI 추천 기능 제거

- **ID**: 009
- **날짜**: 2026-03-17
- **유형**: 기능 추가

## 작업 요약
원장/교사 오늘의 식단 화면에서 "알레르기 주의 아동" 목록과 "대체식품 AI 추천" 기능을 제거. 부모용 AI 저녁 메뉴 추천은 유지.

## 변경 파일 목록
- `src/app/page.note.today/view.pug`: 알레르기 주의 아동 섹션, 대체식품 AI 추천 섹션 제거
- `src/app/page.note.today/view.ts`: allergyAlerts, allergySubstitutes, loadSubstitutes 관련 코드 제거
- `src/app/page.note.today/api.py`: get_today_menu에서 교사/원장용 allergy_alerts 로직 제거
