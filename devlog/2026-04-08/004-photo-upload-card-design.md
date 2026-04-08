# 식단표 사진 업로드 디자인 변경 (하단 카드형)

- **ID**: 004
- **날짜**: 2026-04-08
- **유형**: 기능 추가

## 작업 요약
`page.note.photo`의 공유사진/아이사진 업로드 UI를 기존 호버 시 나타나는 반투명 오버레이 디자인에서 하단 고정 배치형 카드 디자인으로 변경. 업로드/변경/삭제 버튼이 사진 아래에 항상 표시되어 직관적인 UX 제공.

## 변경 파일 목록

### UI (view.pug)
- `src/app/page.note.photo/view.pug`: 공용사진/아이사진 양쪽 모두 `.slot-photo-actions` 오버레이를 `.slot-actions` 하단 버튼으로 교체. 상태별 업로드/변경/삭제 버튼 분리.

### 스타일 (view.scss)
- `src/app/page.note.photo/view.scss`: `.slot-photo-actions` 오버레이 스타일 제거, `.slot-actions` 하단 배치 스타일 추가 (업로드=파란색, 변경=회색, 삭제=빨간색 배경)
