# PWA 설치 안내 페이지 생성 + QR 서버 고유 URL

- **ID**: 003
- **날짜**: 2026-03-16
- **유형**: 기능 추가

## 작업 요약
PWA 설치 안내 페이지(`page.pwa.install`, viewuri: `/install`)를 생성하여 QR 스캔 시 앱 설치 방법을 안내.
아이폰(Safari)과 안드로이드(Chrome) 설치 가이드 제공. QR URL을 서버별 고유 URL(`/install?server_id=X&server_name=Y`)로 변경.

## 변경 파일 목록
### 신규 생성
- `src/app/page.pwa.install/app.json`: viewuri `/install`, controller 빈 문자열 (비로그인 접근 허용)
- `src/app/page.pwa.install/view.pug`: 아이폰/안드로이드 설치 안내 UI
- `src/app/page.pwa.install/view.ts`: query param에서 server_id/server_name 읽기, 로그인 페이지 이동
- `src/app/page.pwa.install/view.scss`: 설치 안내 페이지 스타일

### 수정
- `src/app/page.note/api.py`: `get_qr_code()` QR URL을 `https://child.wizide.com/install?server_id={id}&server_name={name}`으로 변경
