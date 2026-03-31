# 인증번호 재전송 쿨다운 제거

- **ID**: 003
- **날짜**: 2026-03-10
- **유형**: 기능 수정

## 작업 요약
회원가입과 비밀번호 찾기 페이지에서 30초 쿨다운 제거. 재전송 버튼 항상 활성화. 백엔드는 이미 세션 덮어쓰기로 이전 코드 무효화 처리됨.

## 변경 파일 목록
- `src/app/page.forgot/view.ts`: resendCooldown, cooldownTimer, startCooldown() 제거
- `src/app/page.forgot/view.pug`: 쿨다운 조건부 표시 제거, 재전송 버튼 항상 활성화
- `src/app/page.signup/view.ts`: 동일하게 쿨다운 로직 제거 (FN-0002/0003에서 함께 처리)
- `src/app/page.signup/view.pug`: 쿨다운 UI 제거 (FN-0002/0003에서 함께 처리)
