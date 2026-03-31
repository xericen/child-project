# PWA 설치 흐름 개선

- **ID**: 002
- **날짜**: 2026-03-18
- **유형**: 기능 개선

## 작업 요약
PWA 설치 타이머를 2초에서 1초로 변경. 설치 거부 시 수동 설치 가이드를 바로 표시하도록 개선.

## 변경 파일 목록

### App UI
- `page.pwa.install/view.ts`: `setupPWA()` 타이머 2000ms→1000ms. `triggerInstall()` 거부 시 `showFallbackGuide=true` 즉시 설정.
