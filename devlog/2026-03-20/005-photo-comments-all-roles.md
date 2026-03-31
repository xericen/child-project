# 교사/원장 이모티콘·댓글 기능 수정

- **ID**: 005
- **날짜**: 2026-03-20
- **유형**: 버그 수정

## 작업 요약
FN-0004에서 부모 전용으로 구현된 식사 사진 코멘트(이모티콘·텍스트) 기능을 교사·원장도 사용할 수 있도록 role 제한을 제거하였다.

## 변경 파일 목록

### 백엔드
- `src/app/page.note.photo/api.py`
  - `add_comment()`: 기존 부모 전용 role 체크 제거, 로그인 사용자(role 무관) 모두 댓글 작성 가능
  - `get_comments()`: role 체크 없이 로그인 사용자 모두 조회 가능 (기존 유지)

### 프론트엔드
- `src/app/page.note.photo/view.pug`
  - 코멘트 섹션의 `*ngIf` role 제한 제거 → 모든 사용자에게 이모지 바·입력창·댓글 목록 노출
- `src/app/page.note.photo/view.ts`
  - `addEmoji()`, `addComment()` 함수에서 role 체크 제거
