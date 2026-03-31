# Main Page 로그인 기능 구현 (users DB 연동)

- **ID**: 002
- **날짜**: 2026-03-06
- **유형**: 기능 추가

## 작업 요약
Main Page에 users DB를 연동한 로그인 기능 구현. 이메일 미존재/미인증/비밀번호 불일치를 구분하여 에러 메시지 반환.

## 변경 파일 목록

### src/app/page.main/api.py
- `login()` 함수 추가: 이메일 조회 → verified 체크 → 비밀번호 검증 → 세션 설정
- Users 모델 import 추가

### src/app/page.main/view.ts
- `onLogin()` 응답 처리 개선: 서버 에러 메시지 표시, 성공 시 알림 추가
- `service.render()` 호출 추가
