# 회원가입 페이지 역할 선택 UI 토글 버튼 그룹으로 변경

- **ID**: 001
- **날짜**: 2026-04-08
- **유형**: 기능 추가

## 작업 요약
회원가입 페이지(`page.signup`)의 역할 선택 UI를 기존 `<select>` 드롭다운에서 `mat-button-toggle-group` 스타일의 토글 버튼 그룹으로 변경. 부모/교사를 아이콘과 함께 직관적으로 선택할 수 있도록 개선.

## 변경 파일 목록

### UI (view.pug)
- `src/app/page.signup/view.pug`: select 드롭다운을 `.role-toggle-group` 토글 버튼으로 교체

### 스타일 (view.scss)
- `src/app/page.signup/view.scss`: `.role-toggle-group`, `.role-toggle-btn` 스타일 추가 (활성/비활성 상태, hover, 아이콘 애니메이션)

### 로직 (view.ts)
- `src/app/page.signup/view.ts`: `selectRole(role)` 메서드 추가
