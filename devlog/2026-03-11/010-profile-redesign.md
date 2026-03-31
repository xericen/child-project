# 프로필 화면 개편 (교사+어린이 통합)

- **ID**: 010
- **날짜**: 2026-03-11
- **유형**: 기능 추가

## 작업 요약
프로필 페이지를 교사+어린이 통합 화면으로 전면 재설계. 교사 섹션(이름, 소속 반)과 어린이 섹션(이름, 부모 닉네임, 프로필보기)으로 분리 표시. 어린이 카드에서 생년월일 대신 부모 닉네임 표시. 노트 메뉴명 "아이 프로필"→"프로필" 변경 (FN-0008에서 이미 적용).

## 변경 파일 목록
- `src/app/page.note.profile/api.py`: `get_children_list()`→`get_profile_data()`로 변경, 교사 목록(teachers) 반환 추가
- `src/app/page.note.profile/view.ts`: teachers/children 분리 관리, `get_profile_data` 호출
- `src/app/page.note.profile/view.pug`: 교사 섹션 + 어린이 섹션 통합 UI, 닉네임 표시
