# 서버 나가기 + 로그아웃 분리, 가입승인 알림, PNG 업로드 확인

- **ID**: 017
- **날짜**: 2026-03-11
- **유형**: 기능 추가 | 버그 수정

## 작업 요약
1. 헤더 드롭다운에 "서버 나가기" 버튼 추가 — 전체 세션 클리어 후 서버 선택 페이지(`/`)로 이동
2. 로그아웃 동작 변경 — 인증 세션만 클리어하고 서버 정보(join_server_id, join_server_name)는 유지, 로그인 페이지(`/main`)로 이동
3. 회원가입(verify_code) 완료 시 해당 서버의 원장(director)에게 "가입 승인 요청" 알림 전송
4. PNG 업로드 지원 확인 — accept="image/*"로 모든 이미지 형식 지원, curl 테스트로 PNG 업로드 성공 확인

## 변경 파일 목록

### component.header (서버 나가기 + 로그아웃 분리)
- `src/app/component.header/api.py` — `leave_server()` 함수 추가 (전체 세션 클리어), `logout()` 수정 (join_server_id/join_server_name 보존)
- `src/app/component.header/view.ts` — `leaveServer()` 메서드 추가 (→ `/` 이동)
- `src/app/component.header/view.pug` — "서버 나가기 🏫" 버튼 추가, approval 알림 아이콘(📋) 추가
- `src/app/component.header/view.scss` — `.leave-btn` 스타일 추가 (amber 색상)

### page.signup (가입승인 알림)
- `src/app/page.signup/api.py` — `Notifications` 모델 추가, `notify_directors()` 함수 추가, `verify_code()` 내에서 ServerMembers 등록 후 원장에게 알림 전송
