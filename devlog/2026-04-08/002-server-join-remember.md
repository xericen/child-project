# 서버 참여 페이지 - 기기별 서버 코드 기억 기능

- **ID**: 002
- **날짜**: 2026-04-08
- **유형**: 기능 추가

## 작업 요약
`page.server.join` 페이지에 localStorage 기반 서버 코드 기억 기능 추가. 이전에 참여한 어린이집을 카드 형태로 표시하여 클릭만으로 바로 입장 가능. 카드 삭제 기능 및 유효하지 않은 서버 자동 정리 포함.

## 변경 파일 목록

### 로직 (view.ts)
- `src/app/page.server.join/view.ts`: `savedServers` 배열, localStorage 로드/저장, `joinSavedServer()`, `removeSavedServer()` 메서드 추가. 성공적 인증 시 `saveServer()` 호출하여 기록.

### UI (view.pug)
- `src/app/page.server.join/view.pug`: 저장된 서버 카드 목록(`.saved-servers`), 구분선(`.divider-row`) 추가

### 스타일 (view.scss)
- `src/app/page.server.join/view.scss`: 서버 카드, 삭제 버튼, 구분선 스타일 추가
