# 회원정보 비밀번호 변경 기능

- **ID**: 005
- **날짜**: 2026-03-23
- **유형**: 기능 추가

## 작업 요약
회원정보 페이지(`page.myinfo`)에 비밀번호 변경 기능을 추가했다. 현재 비밀번호 확인 후 새 비밀번호로 변경할 수 있으며, 프론트엔드 유효성 검사(길이, 일치 여부)와 백엔드 해싱 처리를 포함한다.

## 변경 파일 목록

### App - page.myinfo
- `api.py`: `change_password()` 함수 추가 (현재 비밀번호 확인 → 새 비밀번호 해싱/저장)
- `view.ts`: 비밀번호 변경 변수(`showPasswordChange`, `currentPassword`, `newPassword`, `confirmPassword`) 및 `togglePasswordChange()`, `changePassword()` 메서드 추가
- `view.pug`: 비밀번호 변경 UI 섹션 추가 (현재 비밀번호 / 새 비밀번호 / 비밀번호 확인 입력 필드)
- `view.scss`: `.password-change-section`, `.pw-toggle-btn` 스타일 추가
