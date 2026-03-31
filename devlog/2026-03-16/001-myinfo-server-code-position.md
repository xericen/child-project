# 원장 회원 정보 서버 회원 코드 표시 위치 수정

- **ID**: 001
- **날짜**: 2026-03-16
- **유형**: UI 개선

## 작업 요약
`page.myinfo`의 서버 회원 코드 필드를 역할(role) 아래에서 이메일 위로 이동하여 더 눈에 잘 띄도록 배치 변경.
서버 생성 로직(`struct/server.py`)과 DB 모델(`db/login_db/servers.py`)에서 `server_code`가 정상적으로 저장·조회되는 것을 확인.

## 변경 파일 목록
### UI
- `src/app/page.myinfo/view.pug`: 서버 회원 코드 `.form-group` 블록을 이메일 필드 위로 이동
