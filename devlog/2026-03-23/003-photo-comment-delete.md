# 사진 댓글 삭제 기능 구현

- **ID**: 003
- **날짜**: 2026-03-23
- **유형**: 기능 추가

## 작업 요약
사진 댓글 삭제 기능을 구현했다. 부모는 본인 작성 댓글만, 교사/원장은 모든 댓글을 삭제할 수 있다. 백엔드에 `delete_comment()` 함수를 추가하고, 프론트엔드에 삭제 버튼(✕)과 삭제 처리 로직을 구현했다.

## 변경 파일 목록

### App - page.note.photo
- `api.py`: `delete_comment()` 함수 추가 (role 기반 권한 — 부모는 본인만, 교사/원장은 모두), `get_role()`에 `user_id` 반환 추가
- `view.ts`: `myUserId` 변수 추가, `deleteComment()` 메서드 추가
- `view.pug`: 댓글 목록에 삭제 버튼(✕) 추가 (role/user_id 조건부 표시)
- `view.scss`: `.comment-delete-btn` 스타일 추가
