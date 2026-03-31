# 서버 선택 랜딩 페이지 구현

- **ID**: 003
- **날짜**: 2026-03-11
- **유형**: 기능 추가

## 작업 요약
루트 URL(`/`)에 서버 선택 페이지를 구현. "child" 제목과 "서버 생성", "참여" 버튼 2개로 구성. 기존 로그인 페이지와 동일한 디자인 템플릿 사용.

## 변경 파일 목록
### App
- `src/app/page.server/app.json` — viewuri: "/"
- `src/app/page.server/view.ts` — goCreate, goJoin 라우팅
- `src/app/page.server/view.pug` — 서버 생성/참여 버튼 UI
- `src/app/page.server/view.scss` — 기존 디자인 템플릿 기반 스타일
