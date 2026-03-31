# QR 코드 제거 및 앱 설치 버튼 추가

- **ID**: 011
- **날짜**: 2026-03-17
- **유형**: 기능 변경

## 작업 요약
note 메인 페이지에서 원장 전용 QR 코드 이미지·생성 기능을 완전 제거하고, 모바일 사용자(역할 무관)에게 PWA 앱 설치 버튼을 표시하도록 변경. Android(Chrome/Edge)는 `beforeinstallprompt` 네이티브 설치 프롬프트, iOS Safari는 3단계 가이드 모달, 기타 브라우저는 `/install` 페이지 fallback으로 분기 처리.

## 변경 파일 목록

### page.note (src/app/page.note/)
| 파일 | 변경 내용 |
|------|----------|
| view.ts | QR 관련 변수/함수(`qrImage`, `qrUrl`, `loadQRCode`) 제거. PWA 설치 로직 추가(`deferredPrompt`, `isMobile`, `isStandalone`, `isIOS`, `showIOSGuide`, `detectDevice`, `setupPWA`, `installApp`, `closeIOSGuide`) |
| view.pug | QR 이미지 섹션 제거. 모바일+비standalone 조건 앱 설치 버튼 추가. iOS 가이드 모달(3단계) 추가 |
| view.scss | QR 관련 스타일(`.qr-image`, `.qr-desc`) 제거. 앱 설치 버튼(`.btn-install`, `.install-icon`, `.install-label`) 및 iOS 가이드 모달(`.ios-guide-overlay`, `.ios-guide-modal`, `.guide-step` 등) 스타일 추가 |
| api.py | `get_qr_code()` 함수 및 `qrcode`/`io`/`base64` import 제거. `get_role()` 함수만 유지 |
