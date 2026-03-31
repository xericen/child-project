# 부모 로그인 후 childcheck 플로우 순서 수정

- **ID**: 002
- **날짜**: 2026-03-25
- **유형**: 버그 수정

## 작업 요약
부모 로그인 후 플로우가 Childcheck → Install → Note 순서로 진행되었으나, 올바른 순서인 Install(step1) → Childcheck(step2) → Note로 수정.

## 변경 파일 목록

### page.main/view.ts
- `navigateAfterLogin()` 로직 순서 변경: install 체크를 childcheck보다 먼저 수행
- Standalone 감지 시 `appInstalled = true`로 설정 후 childcheck 체크로 이어지도록 변경
- 부모인 경우 install 페이지로 이동 시 `childcheck_done` query param 전달

### page.pwa.install/view.ts
- `childcheckDone` 상태 변수 추가: query param `childcheck_done`에서 읽어옴
- `navigateNext()` 메서드 추가: childcheck 미완료 시 `/childcheck`로, 완료 시 `/note`로 이동
- 기존 `/note` 직접 이동을 모두 `navigateNext()`로 변경 (install 승인, standalone, 건너뛰기)

### page.childcheck/view.ts
- `saveChildcheck()` 후 install 체크 로직 제거 (install은 이미 완료된 상태이므로)
- 저장 완료 시 항상 `/note`로 이동
- 불필요한 `isStandalone()`, `appInstalled` 필드 제거
