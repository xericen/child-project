# 날짜 카드 삭제 + 사진 확대 모달 + HWP→PDF 변환

- **ID**: 009
- **날짜**: 2026-03-12
- **유형**: 기능 추가

## 작업 요약
1. 공용/아이 식단표 사진 캘린더에서 날짜 카드 오른쪽 상단에 ✕ 삭제 버튼 추가 (교사/원장만 표시)
2. 학부모 사진 페이지에서 식사 슬롯 사진 클릭 시 모달로 확대 표시, 닫기 버튼으로 복귀
3. 식단 안내 파일 업로드 시 HWP/HWPX 파일을 LibreOffice로 PDF 자동 변환

## 변경 파일 목록

### page.note.photo
- **api.py**: `delete_date_photos()` 함수 추가 — 날짜+카테고리 기준으로 해당 날짜의 모든 사진 일괄 삭제
- **view.ts**: `deleteDatePhotos()`, `openSlotPhoto()`, `closeSlotPhoto()` 메서드 및 `expandedSlot` 상태 변수 추가
- **view.pug**: day-header에 삭제 버튼 추가(canUpload 조건), 사진 확대 모달 오버레이 추가
- **view.scss**: day-header flex 레이아웃, day-delete 버튼 스타일, photo-modal 전체화면 오버레이 스타일 추가

### page.note.meal
- **api.py**: `upload_meal_file()`에 HWP/HWPX→PDF 자동 변환 로직 추가 (subprocess + LibreOffice headless)
