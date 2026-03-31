# HWP 식단 테마뱃지·초록색 알레르기 텍스트 실제 반영

- **ID**: 010
- **날짜**: 2026-03-25
- **유형**: 기능 추가 / 버그 수정

## 작업 요약
DB에 theme/green 마커가 기록되지 않는 원인 파악 및 수정. 실제 HWP 파일을 hwp5html로 변환하여 styles.css 구조를 확인한 결과: CSS 파싱 로직(`charshape-N { color: #008000 }`)은 정상 동작하며, 기존 DB 데이터는 새 파싱 코드 도입 이전에 업로드된 데이터라 재파싱이 필요. 기존 HWP 파일을 재파싱하여 DB를 업데이트하는 `reparse_stored_hwp()` API 함수 추가 및 UI에 "🔄 테마/색상 재파싱" 버튼 추가.

## 변경 파일 목록

### `src/app/page.note.meal/api.py`
- `reparse_stored_hwp()` 함수 추가: 서버에 저장된 HWP 파일을 재파싱하여 meals 테이블의 `content`(green 마커), `theme`, `kcal`, `allergy_numbers` 업데이트

### `src/app/page.note.meal/view.ts`
- `reparseLoading: boolean` 변수 추가
- `reparseHwp()` 메서드 추가: 재파싱 API 호출 후 캘린더/일별 뷰 갱신

### `src/app/page.note.meal/view.pug`
- HWP 파일 표시 영역에 "🔄 테마/색상 재파싱" 버튼 추가

### `src/app/page.note.meal/view.scss`
- `.hwp-file-actions`, `.hwp-file-reparse` 스타일 추가
- `.hwp-file-status` flex-wrap 추가
