# 비밀번호 찾기 Step3 비밀번호 변경 버튼 비활성화 문제 수정

- **ID**: 003
- **날짜**: 2026-03-09
- **유형**: 버그 수정

## 작업 요약
비밀번호 찾기 페이지의 Step3에서 새 비밀번호/비밀번호 확인 입력 시 `service.render()`가 호출되지 않아 `[disabled]` 바인딩이 재평가되지 않는 문제를 수정. view.pug의 Step3 input에 `(ngModelChange)="onPasswordChange()"` 이벤트를 추가하고, view.ts에 `onPasswordChange()` 메서드를 추가하여 입력마다 `service.render()`를 호출하도록 했다.

## 변경 파일 목록
### Page - page.forgot
- `src/app/page.forgot/view.pug`: Step3의 새 비밀번호/비밀번호 확인 input에 `(ngModelChange)="onPasswordChange()"` 추가
- `src/app/page.forgot/view.ts`: `onPasswordChange()` 메서드 추가 (`service.render()` 호출)
