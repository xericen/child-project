# 어린이집 생성 페이지 (3단계 스텝)

- **ID**: 004
- **날짜**: 2026-03-11
- **유형**: 기능 추가

## 작업 요약
어린이집 서버 생성을 위한 3단계 스텝 페이지 구현. Step1: 원장이름+어린이집명, Step2: 이메일+비밀번호, Step3: 인증코드 입력 및 서버 코드 발급. 인증 성공 시 원장 계정(director role) 자동 생성 및 서버 코드 표시.

## 변경 파일 목록
### App
- `src/app/page.server.create/app.json` — viewuri: "/server/create"
- `src/app/page.server.create/view.ts` — 3단계 스텝 로직, 인증코드 입력, verifyAndCreate
- `src/app/page.server.create/view.pug` — 스텝별 폼 UI + 결과 화면 (서버코드 표시)
- `src/app/page.server.create/view.scss` — 스타일 (step-indicator, result-wrap, server-code-box)
- `src/app/page.server.create/api.py` — send_code, resend_code, verify_and_create 함수
