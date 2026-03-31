# PWA 설치 흐름 개선: 타이머 2초, 다운로드 클릭 시 네이티브 설치

- **ID**: 028
- **날짜**: 2026-03-17
- **유형**: 기능 개선

## 작업 요약
Android Chrome에서 PWA 설치 로딩 타이머를 3초→2초로 단축하고, 다운로드 버튼 클릭 시 `beforeinstallprompt`가 아직 미수신이면 수동 가이드 대신 최대 5초간 prompt를 대기한 후 자동으로 네이티브 설치 다이얼로그를 표시하도록 수정.

## 변경 파일 목록
### page.pwa.install/view.ts
- `setupPWA()`: 타이머 3000ms → 2000ms
- `waitForPrompt()`: 새 메서드 추가 — Promise 기반으로 `beforeinstallprompt` 이벤트를 최대 N초 대기
- `onDownloadClick()`: prompt 미수신 시 `waitingForInstall=true` + `waitForPrompt(5000)` 대기 → 수신되면 `triggerInstall()`, 타임아웃 시 수동 가이드
- `triggerInstall()`: 설치 프롬프트 호출 로직 분리
- `promptResolve`: promptHandler에서 대기 중인 Promise resolve

### page.pwa.install/view.pug
- 다운로드 버튼에 `!waitingForInstall` 조건 추가
- `waitingForInstall` 상태 시 "앱 설치 준비 중..." 로딩 표시
