# Note 페이지 리뉴얼 - 역할별 버튼 구성

- **ID**: 008
- **날짜**: 2026-03-09
- **유형**: 기능 추가

## 작업 요약
Note 페이지를 역할별 동적 버튼 구성으로 리뉴얼. 부모: 3개 버튼(오늘의 식단, 식단표, 사진), 교사/원장: 4개 버튼(+아이 프로필). api.py에 get_role() 함수 추가.

## 변경 파일 목록
- `src/app/page.note/view.ts`: 역할 조회 후 menuButtons 동적 구성
- `src/app/page.note/view.pug`: ngFor로 버튼 렌더링
- `src/app/page.note/api.py`: get_role() 함수 추가
