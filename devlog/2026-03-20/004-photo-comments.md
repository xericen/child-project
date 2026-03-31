# 식사 사진 부모 코멘트(이모티콘 반응) 기능

- **ID**: 004
- **날짜**: 2026-03-20
- **유형**: 기능 추가

## 작업 요약
식사 사진에 부모가 간단한 이모티콘/짧은 코멘트를 남길 수 있는 기능을 구현했다. 사진 확대 모달 하단에 이모지 빠른 선택(🙏 😋 👍 ❤️ 😊)과 텍스트 입력(50자 제한)을 배치했다.

## 변경 파일 목록

### DB
- `src/model/db/childcheck/photo_comments.py` (신규): `photo_comments` 테이블 Peewee 모델 (id, photo_id, user_id, content, created_at)
- MySQL: `photo_comments` 테이블 생성 (childcheck DB)

### 백엔드
- `src/app/page.note.photo/api.py`
  - `PhotoComments` 모델 import 추가
  - `get_comments(photo_id)`: 사진별 코멘트 목록 조회 (닉네임 포함)
  - `add_comment(photo_id, content)`: 부모(parent)만 코멘트 작성 가능, 50자 제한

### 프론트엔드
- `src/app/page.note.photo/view.ts`
  - `comments`, `commentText`, `commentLoading`, `quickEmojis` 상태 추가
  - `loadComments()`, `addComment()`, `addEmoji()` 메서드 추가
  - `openSlotPhoto()`: 모달 열 때 코멘트 로드

- `src/app/page.note.photo/view.pug`
  - 모달 하단에 코멘트 섹션 추가 (부모: 이모지바 + 텍스트입력 + 목록, 교사/원장: 읽기 전용 목록)

- `src/app/page.note.photo/view.scss`
  - 코멘트 UI 스타일 (이모지 버튼, 입력 필드, 목록 등)
