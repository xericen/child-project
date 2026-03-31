# 부모 로그인 시 노트 제목에 자녀 이름 표시

- **ID**: 020
- **날짜**: 2026-03-09
- **유형**: 기능 추가

## 작업 요약
page.note 타이틀을 동적으로 변경하여, 부모(role=parent) 로그인 시 자녀 이름이 표시되도록 구현. 교사/원장은 기존 "child" 유지.

## 변경 파일 목록

### page.note
- **api.py**: `get_role()`에서 부모인 경우 `users.child_name` 반환 추가
- **view.ts**: `titleName` 변수 추가, API 응답의 child_name으로 설정
- **view.pug**: `| child` → `| {{ titleName }}` 동적 바인딩
