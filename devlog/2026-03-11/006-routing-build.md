# 루트 URL 라우팅 설정 및 클린 빌드

- **ID**: 006
- **날짜**: 2026-03-11
- **유형**: 설정 변경

## 작업 요약
서버 선택 페이지의 viewuri를 `/`로 설정하여 루트 URL 진입점으로 구성. 새 앱 3개 + api.py 추가로 클린 빌드 수행.

## 변경 파일 목록
### Config
- `src/app/page.server/app.json` — viewuri: "/" (루트 URL)

### Build
- 클린 빌드 수행 (clean: true)
