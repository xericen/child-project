# 프로필 전화번호 줄바꿈 방지

- **ID**: 017
- **날짜**: 2026-03-23
- **유형**: UI 수정

## 작업 요약
프로필 카드에서 "전화번호" 라벨과 "010-xxxx-xxxx" 값이 두 줄로 줄바꿈되는 문제 수정. 2열 그리드의 좁은 카드 너비에서 텍스트가 넘치지 않도록 폰트 사이즈 축소 및 `white-space: nowrap` 적용.

## 변경 파일 목록

### 스타일
- `page.note.profile/view.scss`: `.detail-label` 폰트 0.75rem→0.65rem, `white-space: nowrap`, `flex-shrink: 0`. `.detail-value` 폰트 0.8rem→0.7rem, `white-space: nowrap`, `overflow: hidden`, `text-overflow: ellipsis`. `.detail-row`에 `gap: 6px`, `min-width: 0` 추가.
