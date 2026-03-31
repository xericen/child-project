# 이메일 인증 시스템 개선 (만료시간 + 템플릿 + 개발용 코드 제거)

- **ID**: 001
- **날짜**: 2026-03-19
- **유형**: 기능 추가 / 보안 개선

## 작업 요약
회원가입·비밀번호 재설정의 이메일 인증코드에 10분 만료 기능 추가, child 브랜딩 HTML 이메일 템플릿 적용, 개발용 인증코드 노출(alert/응답 데이터) 제거.

## 변경 파일 목록

### 백엔드 (api.py)
- `src/app/page.signup/api.py`: 인증코드 생성 시 `signup_code_time` 타임스탬프 세션 저장, `verify_code()`에서 10분 초과 시 만료 에러, 이메일 발송 실패 시 code 반환 제거(500 에러로 변경), `_build_code_html()` 공통 HTML 템플릿 함수 추가
- `src/app/page.forgot/api.py`: 동일 패턴 적용 (`forgot_code_time`), 만료 검증, HTML 템플릿, 개발용 code 반환 제거

### 프론트엔드 (view.ts)
- `src/app/page.signup/view.ts`: `sendCode()`/`resendCode()`에서 `email_sent=false` 분기 및 `alert(개발용: code)` 제거
- `src/app/page.forgot/view.ts`: 동일 패턴 제거
