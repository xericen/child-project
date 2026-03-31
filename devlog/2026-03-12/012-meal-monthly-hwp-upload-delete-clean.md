# 식단 월간 HWP 업로드/삭제 UI + 음식명 정리

- **ID**: 012
- **날짜**: 2026-03-12
- **유형**: 기능 추가

## 작업 요약
월간 식단표 페이지에서 HWP 파일 업로드/삭제 UI를 추가하고, 업로드 상태를 표시하도록 개선. HWP 삭제 시 해당 월 식단 데이터 전체 삭제 기능 구현. 음식명에서 알레르기 번호(①②③), 대괄호, 슬래시 등 특수문자를 자동 제거하도록 파싱 로직 개선.

## 변경 파일 목록

### api.py (page.note.meal)
- `_clean_meal_content()` 헬퍼 함수 추가: 원 숫자(①-⑳), 괄호 안 숫자, 대괄호, 슬래시, 한글 뒤 숫자열 제거
- `_parse_meal_html()`에서 `_clean_meal_content()` 호출하여 음식명 자동 정리
- `get_month_hwp()` API 추가: 특정 월의 HWP 파일 존재 여부 조회
- `delete_month_hwp()` API 추가: HWP 파일 삭제 + 해당 월 식단 전체 삭제
- `parse_hwp_meal()` 수정: 파싱 성공 시 HWP 파일 영구 저장 + meta.json에 월별 추적 정보 기록

### view.ts (page.note.meal)
- `monthHwpFile` 상태 변수 추가
- `loadMonthHwp()`: 현재 월의 HWP 파일 상태 조회
- `deleteMonthHwp()`: 확인 후 HWP + 식단 삭제, 월간 데이터 리로드
- 월간 모드 헤더의 `+` 버튼 제거 (별도 업로드 영역으로 대체)

### view.pug (page.note.meal)
- 월간 모드에 HWP 업로드/상태 영역 추가
- 교사/원장 권한 조건 적용

### view.scss (page.note.meal)
- `.hwp-upload-area`: 점선 테두리 업로드 영역 스타일
- `.hwp-file-status`: 업로드 완료 상태 표시 (녹색 테마)
