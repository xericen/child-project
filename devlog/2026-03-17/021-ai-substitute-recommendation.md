# AI 기반 대체 식품 추천 기능

- **ID**: 021
- **날짜**: 2026-03-17
- **유형**: 기능 추가

## 작업 요약
알레르기 주의 아동 팝업에서 각 아동별 "대체 식품 추천" 버튼을 추가하여 Gemini AI가 이번 주 식단에서 알레르기 유발 메뉴의 대체 메뉴를 추천하도록 구현.

## 변경 파일 목록
- `src/app/component.header/api.py` — get_substitute_recommendation() 함수 추가: 주간 식단 + 알레르기 정보 + AllergyCategories.substitute_foods를 Gemini AI에 전달, JSON 배열 형태 응답
- `src/app/component.header/view.ts` — substituteLoading/substituteResults 상태, getSubstitute()/hasSubstitute()/getSubstituteList()/isSubstituteLoading() 메서드 추가
- `src/app/component.header/view.pug` — 각 알레르기 항목에 "대체 식품 추천" 버튼 + AI 결과 표시 (original→substitute, reason)
- `src/app/component.header/view.scss` — .substitute-section, .btn-substitute, .substitute-list, .substitute-item, .sub-row 등 스타일
