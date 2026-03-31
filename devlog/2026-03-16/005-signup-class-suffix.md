# 회원가입 - 반 입력 접미사 "반" 고정 표시

- **ID**: 005
- **날짜**: 2026-03-16
- **유형**: UI 개선

## 작업 요약
회원가입 페이지(`page.signup`)의 부모용 "자녀 반"과 교사용 "담당 반" 입력란에 "반" 접미사를 고정 표시.
사용자는 "강아지"만 입력하면 API 전송 시 자동으로 "강아지반"으로 조합.

## 변경 파일 목록
### UI
- `src/app/page.signup/view.pug`: 부모·교사 반 입력란을 `.input-group` + `span.input-suffix` 구조로 변경, placeholder "햇살"로 수정
- `src/app/page.signup/view.scss`: `.input-group`, `.input-suffix` 스타일 추가
- `src/app/page.signup/view.ts`: `sendCode()`에서 `class_name`을 `className + '반'`으로 조합
