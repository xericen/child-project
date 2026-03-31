# 사진 페이지 사진 첨부 기능 구현

- **ID**: 015
- **날짜**: 2026-03-09
- **유형**: 기능 추가

## 작업 요약
photos DB 테이블 신규 생성. page.note.photo에 모드 전환(menu/list) 구현. 공용사진/아이사진 카테고리별 사진 목록, 사진 업로드 폼(교사/원장만), 삭제 기능 구현.

## 변경 파일 목록
- `src/model/db/childcheck/photos.py` — 신규: photos Peewee 모델
- `src/app/page.note.photo/view.ts` — 모드 전환, 사진 업로드/조회/삭제
- `src/app/page.note.photo/view.pug` — 카테고리 메뉴, 사진 그리드, 업로드 폼
- `src/app/page.note.photo/view.scss` — 사진 그리드, 업로드 폼 스타일
- `src/app/page.note.photo/api.py` — get_photos, upload_photo, delete_photo
