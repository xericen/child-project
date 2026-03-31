# 앱 진입 오류 수정 + 자동 로그인 라우팅 개선

- **ID**: 006
- **날짜**: 2026-03-20
- **유형**: 버그 수정

## 작업 요약
PWA 앱 진입 시 세션 만료로 "child Note" 오류 표시되는 문제와, 자동 로그인 시 중간 화면이 깜빡이는 라우팅 문제를 수정했다.

## 변경 파일 목록

### page.server (자동 로그인 체크 추가)
- `view.ts`: localStorage에서 `child_auto_login` + `child_server_info` 확인, 둘 다 있으면 `/main`으로 즉시 이동. `isLoading` 플래그로 UI 깜빡임 방지
- `view.pug`: `*ngIf="!isLoading"` 래퍼 추가

### page.main (서버 정보 저장 + UI 깜빡임 방지)
- `view.ts`: `isLoading` 플래그 추가, `saveServerInfo()` 메서드로 서버 정보를 localStorage에 저장, `tryAutoLogin()` 반환값 기반 렌더 스킵
- `view.pug`: `*ngIf="!isLoading"` 래퍼 추가

### page.note (401 처리)
- `view.ts`: `loadRole()`에서 401 응답 시 localStorage 정리 후 `/`로 리다이렉트
