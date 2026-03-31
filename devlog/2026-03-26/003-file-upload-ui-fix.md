# 식단 안내 파일 선택 UI 정렬 수정

- **ID**: 003
- **날짜**: 2026-03-26
- **유형**: 버그 수정

## 작업 요약
식단표 페이지의 파일 업로드 영역(select + file input + button)이 모바일(360px) 화면에서 flex-wrap으로 어색하게 줄바꿈되던 문제 수정. 월 선택 select를 상단 full-width, 파일 선택 + 업로드 버튼을 하단 한 줄로 2행 배치 구조로 변경.

## 변경 파일 목록
### UI (view.pug)
- `src/app/page.note.meal/view.pug`: `.file-upload-row` 내부를 select + `.file-upload-input-row`(file input + button) 2행 구조로 변경

### 스타일 (view.scss)
- `src/app/page.note.meal/view.scss`: `.file-upload-row`를 `flex-direction: column`으로 변경, `.file-upload-input-row` 추가 (flex row), `.file-month-select`를 `width: 100%`로 변경
