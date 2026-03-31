# PWA manifest.json / sw.js / index.pug 설정

- **ID**: 016
- **날짜**: 2026-03-17
- **유형**: 기능 추가

## 작업 요약
PWA 설치를 위한 필수 인프라(manifest.json, Service Worker, HTML meta 태그)를 구성했다. Android Chrome에서 `beforeinstallprompt` 이벤트가 발생하여 네이티브 설치 프롬프트가 동작하도록 했다.

## 변경 파일 목록

### 신규 생성
- `src/assets/manifest.json`: PWA Web App Manifest (name, icons, display, theme_color 등)
- `config/pwa/sw.js`: Service Worker (기본 pass-through, 패키지 route `/sw.js`가 읽어서 서빙)

### 수정
- `src/angular/index.pug`: manifest link(`/assets/manifest.json`), theme-color, apple-mobile-web-app meta 태그, SW 등록 스크립트 추가

### 시도 후 폐기
- Source route `route/pwa.manifest` → 정적 파일 서빙보다 우선순위가 낮아 SPA fallback으로 빠짐 → 삭제
- Package route `portal/season/route/pwa.manifest` → 동일 문제 → 삭제
- `angular.build.options.json` assets 설정 → ngc-esbuild가 미지원 → 원복

### 최종 서빙 구조
- `/assets/manifest.json` → `src/assets/` 정적 파일 서빙 (application/json)
- `/sw.js` → 기존 패키지 route `portal.season.pwa.swjs`가 `config/pwa/sw.js` 읽어서 서빙 (text/javascript)
