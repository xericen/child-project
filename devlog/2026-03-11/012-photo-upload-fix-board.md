# 사진 업로드 버튼 수정 + 게시판형 레이아웃

- **ID**: 012
- **날짜**: 2026-03-11
- **유형**: 버그 수정 + 기능 추가

## 작업 요약
사진 업로드 시 wiz.call()이 FormData 파일을 처리하지 못하는 문제를 fetch() 직접 호출로 수정. 사진 목록을 게시판형(날짜/제목/사진) 레이아웃으로 변경.

## 변경 파일 목록
- `src/app/page.note.photo/view.ts`: uploadPhoto()에서 wiz.call() → fetch() 변경, selectedFile 상태 render 추가
- `src/app/page.note.photo/view.pug`: 게시판형 레이아웃(.board-item/.board-header/.board-image), 파일 선택 상태 표시, disabled 버튼
- `src/app/page.note.photo/view.scss`: 게시판형 스타일(.board-*), 업로드 버튼 disabled 스타일
- `src/app/page.note.photo/api.py`: get_photos()에 created_at 포맷팅 추가
