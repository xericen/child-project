# 저녁 추천 AI 분석 결과 미표시 수정

- **ID**: 009
- **날짜**: 2026-03-25
- **유형**: 버그 수정

## 작업 요약
저녁 추천 버튼 클릭 시 "추천을 가져오지 못했습니다." 에러만 표시되는 문제 수정. `gemini.ask_json()`이 JSON 파싱 실패 시 raw 텍스트(string)를 반환하여 `isinstance(result, dict)` 검사 실패로 에러로 처리되던 것을 `None` 반환으로 수정. `result` 변수 초기화 누락 및 에러 메시지 개선.

## 변경 파일 목록

### `src/model/gemini.py`
- `ask_json()`: JSON 파싱 실패 시 raw 텍스트 반환 → `None` 반환으로 변경

### `src/app/page.note.today/api.py`
- `recommend_dinner()`: try 블록 전 `result = None` 초기화 추가
- 에러 메시지를 실제 예외 내용 포함 및 좀 더 명확한 문구로 개선
