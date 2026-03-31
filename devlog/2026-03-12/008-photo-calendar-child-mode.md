# 식단 사진 공용/아이 캘린더 통합 UI 개선

- **ID**: 008
- **날짜**: 2026-03-12
- **유형**: 기능 추가

## 작업 요약
아이 맞춤 식단 사진을 기존 게시판형(리스트) UI에서 공용 식단표와 동일한 캘린더(슬롯) 방식으로 전환. 공용/아이 캘린더에서 슬롯 업로드 코드를 공유화하고, 사진 업로드 후 즉시 UI 반영(FN-0007) 및 아이 카테고리 upsert 지원 추가.

## 변경 파일 목록

### page.note.photo/api.py
- `_build_days_response()` 헬퍼 함수 추가 (공용/아이 공통 날짜 그룹핑 로직)
- `get_child_photos()` 신규 함수 추가 (아이별 + 월별 + meal_type 그룹핑)
- `upload_photo()`: 아이 카테고리도 날짜+meal_type+target_user_id 기반 upsert(교체) 로직 추가

### page.note.photo/view.ts
- `childDays`, `childYear`, `childMonth` 상태 변수 추가
- `pendingCategory` 상태 추가 (공용/아이 업로드 구분)
- `loadChildPhotos()`, `prevChildMonth()`, `nextChildMonth()`, `getChildMonthLabel()`, `getChildCalendarTitle()` 메서드 추가
- `onSlotUploadClick()`, `onSlotFileSelected()`, `deleteSlotPhoto()`: category 매개변수 추가로 공용/아이 공유
- `selectChild()`: list 모드 → child_calendar 모드로 변경
- `goChildPhotos()`: 부모인 경우 바로 child_calendar 모드 진입
- `goBack()`: child_calendar 모드 뒤로가기 처리 추가
- 기존 list 모드 관련 코드 제거 (loadPhotos, toggleUpload, uploadPhoto, onFileSelect 등)

### page.note.photo/view.pug
- `mode === 'list'` 섹션 제거 (게시판형 UI 제거)
- `mode === 'child_calendar'` 섹션 추가 (공용 캘린더와 동일 구조)
- 공용/아이 캘린더 슬롯에 category 매개변수 전달
