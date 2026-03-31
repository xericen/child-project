# 식단 안내 파일 UI 간소화

- **ID**: 018
- **날짜**: 2026-03-23
- **유형**: UI 수정

## 작업 요약
식단 안내 파일 목록의 `.file-item`에서 박스 스타일(border, background, border-radius)을 제거하고 심플한 파일 리스트 형태로 변경. 파일 아이콘+이름이 바로 보이도록 깔끔하게 스타일링.

## 변경 파일 목록

### 스타일
- `page.note.meal/view.scss`: `.file-item`에서 `background`, `border-radius`, `border` 제거. 패딩 축소(8px 10px → 4px 0).
