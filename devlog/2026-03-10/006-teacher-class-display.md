# 교사 로그인 시 반 정보 표시

- **ID**: 006
- **날짜**: 2026-03-10
- **유형**: 기능 추가

## 작업 요약
교사 로그인 시 note 페이지 제목 위에 담당 반(class_name) 정보를 배지로 표시. 원장에게는 가입 승인 메뉴 추가.

## 변경 파일 목록
- `src/app/page.note/api.py`: get_role()에서 교사일 때 class_name 반환
- `src/app/page.note/view.ts`: className 변수 추가, 교사일 때 저장, 원장 승인 메뉴 추가
- `src/app/page.note/view.pug`: class-badge 표시
- `src/app/page.note/view.scss`: .class-badge 스타일 추가
