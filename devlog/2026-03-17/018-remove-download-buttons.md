# 모든 페이지에서 Download 버튼 및 PWA 코드 삭제

- **ID**: 018
- **날짜**: 2026-03-17
- **유형**: 리팩토링

## 작업 요약
page.note에서 Download 버튼, PWA 감지/설치 로직, iOS 가이드 모달 등 관련 코드를 모두 제거함.

## 변경 파일 목록
- `src/app/page.note/view.pug` — .download-area 및 iOS 가이드 모달 코드 삭제
- `src/app/page.note/view.ts` — PWA 관련 프로퍼티/메서드 전부 삭제 (isMobile, deferredPrompt, canInstallPWA, showIOSGuide, isIOS, isStandalone, detectDevice, setupPWA, installApp, closeIOSGuide)
- `src/app/page.note/view.scss` — .download-area, .btn-download, iOS 가이드 모달 스타일 삭제
