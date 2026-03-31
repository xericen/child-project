# childcheck 페이지 미표시 버그 수정

- **ID**: 008
- **날짜**: 2026-03-25
- **유형**: 버그 수정

## 작업 요약
부모 로그인 후 childcheck 페이지가 표시되지 않는 버그 수정. `page.pwa.install/view.ts`의 `childcheckDone` 기본값이 `true`로 설정되어 있어, 쿼리 파라미터 없이 install 페이지에 접근하면 항상 `/note`로 이동하던 문제 수정. 또한 교사/원장 역할에 `childcheck_done=true` 파라미터를 명시적으로 전달하지 않아 기본값 처리가 꼬이던 문제도 수정.

## 변경 파일 목록

### `src/app/page.pwa.install/view.ts`
- `childcheckDone` 초기값 `true` → `false` 변경
- 파라미터 파싱: `!== 'false'` → `=== 'true'` (파라미터 없으면 false로 처리)

### `src/app/page.main/view.ts`
- `navigateAfterLogin()` 내 queryParams: 부모만 전달하던 방식 → 모든 역할에 `childcheck_done` 전달
- 교사/원장: 항상 `childcheck_done=true`, 부모 미완료 시 `false`
