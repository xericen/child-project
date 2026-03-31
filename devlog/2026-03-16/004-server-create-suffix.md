# 어린이집 서버 생성 - 어린이집명 접미사 고정 표시

- **ID**: 004
- **날짜**: 2026-03-16
- **유형**: UI 개선

## 작업 요약
어린이집 서버 생성 페이지(`page.server.create`)의 어린이집명 입력란에 "어린이집" 접미사를 고정 표시.
사용자는 "사랑송송"만 입력하면 되고, API 전송 시 자동으로 "사랑송송 어린이집"으로 조합하여 전달.

## 변경 파일 목록
### UI
- `src/app/page.server.create/view.pug`: 어린이집명 입력란을 `.input-group` 구조로 변경, `span.input-suffix` 추가
- `src/app/page.server.create/view.scss`: `.input-group`, `.input-suffix` 스타일 추가
- `src/app/page.server.create/view.ts`: `sendCode()`에서 `server_name`을 `serverName + ' 어린이집'`으로 조합하여 전달
