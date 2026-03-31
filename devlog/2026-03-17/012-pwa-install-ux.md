# PWA 설치 안내 페이지 UX 전면 개선

- **ID**: 012
- **날짜**: 2026-03-17
- **유형**: 기능 개선

## 작업 요약
page.pwa.install 페이지를 정적 가이드에서 브라우저/OS 자동 감지 기반 동적 설치 안내 페이지로 전면 개선. 커스텀 설치 확인 모달을 추가하여 "취소"/"다운로드" 버튼 라벨을 적용하고 beforeinstallprompt 네이티브 설치를 연동함.

## 변경 파일 목록

### page.pwa.install (src/app/page.pwa.install/)
| 파일 | 변경 내용 |
|------|----------|
| view.ts | 디바이스/브라우저 자동 감지(iOS, Android, PC, Safari, Chrome, Samsung Internet, iOS Chrome), beforeinstallprompt 이벤트 캡처, 커스텀 확인 모달 로직(confirmInstall/cancelInstall), standalone 감지 |
| view.pug | 시나리오별 조건 분기: (1) 이미 설치됨 안내, (2) 설치 완료 안내, (3) Android 다운로드 버튼, (4) iOS Safari 3단계 가이드, (5) iOS Chrome → Safari 안내, (6) Samsung Internet 가이드, (7) Android 기타 → Chrome 안내, (8) PC → 모바일 접속 안내. 커스텀 확인 모달("취소"/"다운로드") 추가 |
| view.scss | 가이드 섹션/다운로드 버튼/단계별 아이템/URL 박스/커스텀 확인 모달 스타일 전면 재작성 |
