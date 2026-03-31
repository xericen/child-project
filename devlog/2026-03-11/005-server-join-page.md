# 서버 참여 페이지 구현

- **ID**: 005
- **날짜**: 2026-03-11
- **유형**: 기능 추가

## 작업 요약
서버 회원번호를 입력하여 어린이집에 참여하는 페이지 구현. 코드 유효성 검증 후 세션에 server_id를 저장하고 회원가입 페이지로 이동.

## 변경 파일 목록
### App
- `src/app/page.server.join/app.json` — viewuri: "/server/join"
- `src/app/page.server.join/view.ts` — 코드 입력 및 검증 로직
- `src/app/page.server.join/view.pug` — 코드 입력 폼 UI
- `src/app/page.server.join/view.scss` — 스타일
- `src/app/page.server.join/api.py` — verify_server_code 함수
