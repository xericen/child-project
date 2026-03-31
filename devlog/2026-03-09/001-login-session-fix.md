# 로그인 페이지 세션 저장 문제 수정

- **ID**: 001
- **날짜**: 2026-03-09
- **유형**: 버그 수정

## 작업 요약
page.main의 app.json에서 `"controller": ""`로 설정되어 있어 base controller가 실행되지 않았고, `wiz.session` 초기화가 누락되어 로그인 시 `AttributeError: 'Wiz' object has no attribute 'session'` 에러가 발생했다. `"controller": "base"`로 수정하여 해결.

## 변경 파일 목록
### App 설정
- `src/app/page.main/app.json`: `"controller": ""` → `"controller": "base"` 변경
