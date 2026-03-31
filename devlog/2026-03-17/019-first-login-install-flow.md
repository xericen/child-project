# 첫 로그인 시 앱 다운로드 안내 페이지 유도

- **ID**: 019
- **날짜**: 2026-03-17
- **유형**: 기능 추가

## 작업 요약
로그인 성공 후 PWA 미설치 상태(!isStandalone)이면 /install 페이지로 자동 이동하도록 흐름 변경. childcheck 완료 후에도 동일 로직 적용. install 페이지에 건너뛰기 버튼과 시작하기 버튼 추가.

## 변경 파일 목록
- `src/app/page.main/view.ts` — isStandalone() 메서드 추가, navigateAfterLogin()에서 role별 /install 분기 로직
- `src/app/page.childcheck/view.ts` — saveChildcheck() 완료 후 isStandalone() 체크하여 /install 또는 /note로 분기
- `src/app/page.pwa.install/view.ts` — goToNote() 메서드 추가
- `src/app/page.pwa.install/view.pug` — 건너뛰기 버튼, 시작하기 버튼 추가
- `src/app/page.pwa.install/view.scss` — .btn-skip, .btn-start, .skip-section 스타일 추가
