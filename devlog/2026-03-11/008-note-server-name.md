# 원장 노트 화면에 어린이집 이름 표시

- **ID**: 008
- **날짜**: 2026-03-11
- **유형**: 기능 추가

## 작업 요약
원장(director) 역할의 노트 메인 화면에 현재 접속한 어린이집 이름이 표시되도록 수정. 세션의 `join_server_name`을 API에서 반환하고 UI에 표시. 메뉴명도 "아이 프로필"→"프로필"로 변경.

## 변경 파일 목록
- `src/app/page.note/api.py`: `get_role()`에 `server_name` 반환 추가
- `src/app/page.note/view.ts`: `serverName` 변수 추가, `loadRole()`에서 세팅, 메뉴명 변경
- `src/app/page.note/view.pug`: 어린이집 이름 배지 표시 (serverName 우선, 없으면 className)
