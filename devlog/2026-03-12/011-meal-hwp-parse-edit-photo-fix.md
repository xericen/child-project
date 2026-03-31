# 식단 HWP 파싱/수정 + 사진 삭제 버그 수정

- **ID**: 011
- **날짜**: 2026-03-12
- **유형**: 기능 추가 / 버그 수정

## 작업 요약
사진 페이지의 날짜 카드 삭제 버그 수정(로컬 배열 즉시 제거), 식단 안내 파일 HWP→PDF 변환 제거(원본 그대로 제공), 월간 식단표에 + 버튼 추가하여 HWP 파일 업로드 시 식단표 자동 파싱/DB 입력 기능 구현, 날짜별 식단 수정(인라인 편집) 기능 추가.

## 변경 파일 목록

### 사진 페이지 (page.note.photo)
- `view.ts`: `deleteDatePhotos()` - 로컬 배열에서 즉시 제거 후 서버 삭제, UI 즉시 반영

### 식단 페이지 (page.note.meal)
- `api.py`:
  - `upload_meal_file()`: HWP→PDF 변환 코드 제거, 원본 파일 그대로 저장
  - `update_meal()`: 신규 - 식단 수정 API (meal_type, content 업데이트)
  - `parse_hwp_meal()`: 신규 - HWP 파일 업로드 → LibreOffice HTML 변환 → BS4 파싱 → DB 자동 입력
  - `_parse_meal_html()`: 신규 - HTML 테이블에서 식단 데이터 추출 (년월 인식, 주차별 일자/오전간식/점심/오후간식 파싱)
- `view.ts`:
  - HWP 파싱: `triggerHwpUpload()`, `onHwpFileSelected()`, `hwpLoading` 상태
  - 식단 수정: `startEdit()`, `cancelEdit()`, `updateMeal()`, `editingMealId/editMealType/editMealContent` 상태
- `view.pug`:
  - 숨김 HWP 파일 입력 추가
  - 월간 모드 헤더에 + 버튼 (HWP 업로드 트리거)
  - HWP 파싱 로딩 오버레이
  - 식단 카드에 수정(✎)/삭제(✕) 버튼 및 인라인 수정 폼
- `view.scss`:
  - `.hwp-loading`, `.meal-actions`, `.meal-edit`, `.edit-form`, `.edit-actions`, `.btn-edit-save`, `.btn-edit-cancel` 스타일 추가
