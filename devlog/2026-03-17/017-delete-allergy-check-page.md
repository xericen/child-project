# 알레르기 체크 페이지 삭제 및 메뉴 버튼 제거

- **ID**: 017
- **날짜**: 2026-03-17
- **유형**: 리팩토링

## 작업 요약
알레르기 체크 전용 페이지(`page.note.allergy`)를 삭제하고, note 메인 메뉴의 `buildMenu()`에서 해당 버튼을 제거함.

## 변경 파일 목록
- `src/app/page.note.allergy/` — 앱 전체 삭제
- `src/app/page.note/view.ts` — buildMenu()에서 '⚠️ 알레르기 체크' 버튼 제거 (teacher, director 분기)
