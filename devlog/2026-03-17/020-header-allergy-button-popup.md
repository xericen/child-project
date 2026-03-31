# 알레르기 카테고리 매칭 로직 수정 + 헤더 알레르기 버튼/팝업

- **ID**: 020
- **날짜**: 2026-03-17
- **유형**: 기능 추가 + 버그 수정

## 작업 요약
FN-0015 + FN-0016 통합 구현. 기타 알레르기(other_detail)의 각 키워드를 AllergyCategories의 caution_foods와 개별 매칭하여 정확한 카테고리명으로 표시하도록 수정. component.header에 ⚠️ 버튼과 알레르기 주의 아동 팝업 추가 (교사/원장 전용).

## 변경 파일 목록
- `src/app/component.header/api.py` — Meals/Children/ChildAllergies/AllergyCategories/ServerMembers 모델 임포트, _get_server_id(), _build_caution_food_map(), get_weekly_allergy() 함수 추가. 기타 알레르기 키워드별 개별 카테고리 매칭 로직 구현.
- `src/app/component.header/view.ts` — showAllergyPanel, allergyAlerts, allergyCount 프로퍼티 추가, loadAllergyAlerts(), toggleAllergyPanel() 메서드 추가. teacher/director일 때만 로드.
- `src/app/component.header/view.pug` — ⚠️ 버튼 (🔔 왼쪽), 알레르기 패널 UI (아동별 알레르기 종류, 해당 식단 표시)
- `src/app/component.header/view.scss` — .allergy-panel, .allergy-item, .allergy-badge 등 스타일 추가
