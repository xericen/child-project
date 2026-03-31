# 공용 식단표 사진 캘린더형 리디자인

- **ID**: 006
- **날짜**: 2026-03-12
- **유형**: 기능 추가

## 작업 요약
공용 식단표 사진 화면을 캘린더형 레이아웃으로 리디자인. 월 네비게이션(◁ YYYY년 MM월 ▷)으로 월별 조회, 각 날짜 카드에 오전간식/점심식사/오후간식 3슬롯 표시. 교사/원장은 빈 슬롯의 +버튼으로 사진 업로드, 사진 위 ✕버튼으로 삭제 가능.

## 변경 파일 목록

### DB 스키마
- `src/model/db/childcheck/photos.py`: `meal_type`(VARCHAR 20), `photo_date`(DATE) 컬럼 추가
- ALTER TABLE photos ADD COLUMN meal_type, photo_date 실행

### 백엔드 API
- `src/app/page.note.photo/api.py`:
  - `get_public_photos()` 신규: year/month 파라미터로 월별 조회, 날짜별 3슬롯 그룹핑 반환
  - `upload_photo()` 수정: meal_type, photo_date 파라미터 지원, 동일 날짜+타입 사진 교체 로직
  - `delete_photo()` 수정: 파일 시스템 실제 파일도 삭제

### 프론트엔드
- `src/app/page.note.photo/view.ts`: 캘린더 모드(public_calendar) 상태관리, 월 네비게이션, 슬롯별 업로드/삭제
- `src/app/page.note.photo/view.pug`: 월 nav + 날짜 카드 + 3슬롯 레이아웃, 숨겨진 file input
- `src/app/page.note.photo/view.scss`: 월 nav, 날짜 카드, 슬롯 헤더 색상(노랑/주황/빨강 그라데이션), 사진/플레이스홀더 스타일
