# 원장 Note 제목 변경 + 배지 색상 분리

- **ID**: 011
- **날짜**: 2026-03-11
- **유형**: 기능 추가

## 작업 요약
원장 로그인 시 note 화면 제목을 `director Note`로 변경. 어린이집명 배지(파란색 #5b6ef5)와 반명 배지(주황색 #f59e42) 색상을 분리하여 구분 가능하도록 수정.

## 변경 파일 목록
- `src/app/page.note/view.ts`: 원장 role일 때 titleName을 'director'로 설정
- `src/app/page.note/view.pug`: serverName 배지에 `.server-badge` 클래스 적용, className 배지에 `.class-badge` 유지
- `src/app/page.note/view.scss`: `.server-badge`(파란색), `.class-badge`(주황색) 스타일 분리
