# 회원가입 시 자녀이름 저장 수정

- **ID**: 005
- **날짜**: 2026-03-09
- **유형**: 버그 수정

## 작업 요약
회원가입 시 UI에서 수집하는 자녀이름(childName)이 서버로 전송되지 않던 문제 수정. signup/view.ts sendCode()에 child_name 파라미터 추가, api.py send_code()에서 child_name 수신 및 저장. verify_code()에서 role 반환하여 역할별 리다이렉트 지원.

## 변경 파일 목록
- `src/app/page.signup/view.ts`: sendCode()에 child_name 전송, verifyCode()에 역할별 리다이렉트(parent→/childcheck, 기타→/note)
- `src/app/page.signup/api.py`: send_code()에 child_name 수신/저장, verify_code()에 role 반환
