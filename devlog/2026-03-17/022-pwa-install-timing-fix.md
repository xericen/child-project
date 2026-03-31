# Android PWA 설치 페이지 타이밍 문제 수정

- **ID**: 022
- **날짜**: 2026-03-17
- **유형**: 버그 수정

## 작업 요약
Android Chrome에서 PWA install 페이지 첫 진입 시 `beforeinstallprompt` 이벤트가 비동기로 발생하여 다운로드 버튼 대신 fallback 안내가 먼저 표시되는 문제 수정. `waitingForPrompt` 상태와 3초 타임아웃으로 로딩→다운로드 버튼 전환 구현.

## 변경 파일 목록
### page.pwa.install
- **view.ts**: `waitingForPrompt` 프로퍼티 추가, `setupPWA()`에 3초 타임아웃 로직, `ngOnDestroy()`에서 타임아웃 클리어
- **view.pug**: 대기 중 로딩 UI 추가, 모든 가이드 섹션에 `!waitingForPrompt` 조건 추가, 단계 텍스트 단축
- **view.scss**: `.loading-spinner` + `.spinner` 스타일 추가, `.step-content` overflow 수정 (`word-break: break-all`, `overflow-wrap: break-word`)
