# 교사/원장 날짜별 식단 — 대체식 체크박스 UI & API

- **ID**: 003
- **날짜**: 2026-04-07
- **유형**: 기능 추가

## 작업 요약
교사/원장의 날짜별 식단 보기에서 green 마커(대체식) 항목 옆에 체크박스를 추가하여, 대체식 사용 여부를 저장할 수 있도록 했다.

## 변경 파일 목록
### 백엔드
- `src/app/page.note.meal/api.py`
  - `MealSubstituteSelections` 모델 로딩 추가
  - `_parse_substitute_pairs()` 헬퍼 — content에서 (원본, 대체) 쌍 추출
  - `get_daily()` — substitute_pairs + 선택상태 포함하여 반환
  - `toggle_substitute()` — 대체식 선택 토글 API (신규 함수)

### 프론트엔드
- `src/app/page.note.meal/view.ts`
  - `parseMealLines()` — content를 줄별로 파싱하여 구조화
  - `isSubstituteSelected()` — 선택 상태 조회
  - `toggleSubstitute()` — 체크 토글 → API 호출
- `src/app/page.note.meal/view.pug`
  - daily 모드: 교사/원장에게 체크박스(☐/☑) UI 표시, 부모에게 green 텍스트 표시
- `src/app/page.note.meal/view.scss`
  - `.sub-row`, `.sub-check`, `.sub-strikethrough`, `.sub-substitute` 등 스타일 추가
