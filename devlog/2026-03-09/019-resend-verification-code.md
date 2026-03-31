# 회원가입/비밀번호찾기 인증번호 재전송 기능

- **ID**: 019
- **날짜**: 2026-03-09
- **유형**: 기능 추가

## 작업 요약
회원가입(page.signup)과 비밀번호 찾기(page.forgot) 페이지의 인증코드 입력 단계에 "인증번호 재전송" 버튼을 추가했다. 30초 쿨다운 타이머를 적용하여 반복 요청을 방지하고, 재전송 시 기존 세션 코드를 새 코드로 덮어쓴다.

## 변경 파일 목록

### page.signup
- **api.py**: `resend_code()` 함수 추가
- **view.ts**: `resendCooldown`, `cooldownTimer`, `resendCode()`, `startCooldown()` 추가
- **view.pug**: step-3에 `.resend-wrap` 블록 추가
- **view.scss**: `.resend-wrap`, `.resend-btn` 스타일 추가

### page.forgot
- **api.py**: `resend_code()` 함수 추가
- **view.ts**: `resendCooldown`, `cooldownTimer`, `resendCode()`, `startCooldown()` 추가
- **view.pug**: step-2에 `.resend-wrap` 블록 추가
- **view.scss**: `.resend-wrap`, `.resend-btn` 스타일 추가
