# HWP 직접 파싱으로 전환 (LibreOffice → pyhwp)

- **ID**: 009
- **날짜**: 2026-03-23
- **유형**: 기능 수정

## 작업 요약
HWP 식단표 파싱을 LibreOffice HTML 변환 방식에서 pyhwp(hwp5html) 기반 XHTML 직접 변환으로 전환. rowspan/colspan을 column-position 추적으로 정확히 처리하여 대체공휴일 등 병합 셀에서도 날짜-식단 매핑이 정확하도록 개선.

## 변경 파일 목록

### 백엔드
- `src/app/page.note.meal/api.py`
  - `import tempfile, shutil` 추가
  - `_parse_meal_html()`: 전면 재작성 — column-position 기반 rowspan/colspan 처리로 정확한 셀-날짜 매핑
  - `parse_hwp_meal()`: LibreOffice 변환 → `hwp5html` CLI 변환으로 교체, 임시 디렉토리 사용

### 패키지 설치
- `pyhwp` (pip): HWP5 포맷 직접 파싱 라이브러리 (hwp5html CLI 포함)
