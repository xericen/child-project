# 프로필 카드 이모티콘/이름 반반 비율 조정

- **ID**: 001
- **날짜**: 2026-03-12
- **유형**: UI 수정

## 작업 요약
아이 프로필 카드에서 이모티콘(👶)이 이름에 비해 너무 크게 표시되던 문제를 수정. `.card-avatar`와 `.card-info`를 각각 `flex: 1`로 설정하여 50:50 비율로 조정.

## 변경 파일 목록
- `src/app/page.note.profile/view.scss`: `.card-avatar`를 고정 크기(40x40)에서 `flex: 1`로 변경, `.card-info`에 `flex: 1` 추가, `.card-top` gap/padding 미세 조정
