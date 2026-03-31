# 통계 수치 불안정 원인 분석 및 충족률 상세화

- **ID**: 015
- **날짜**: 2026-03-23
- **유형**: 버그 수정 + 기능 개선

## 작업 요약
식단 통계를 볼 때마다 수치가 달라지는 문제의 원인을 파악하고 수정. AI 영양 분석(`get_ai_analysis`)이 매 요청마다 Gemini API를 호출하여 매번 다른 추정치를 반환하는 것이 원인. 식단 데이터 해시 기반 캐싱을 도입하여 동일 식단이면 같은 분석 결과를 반환하도록 수정. 영양소 충족률 표시도 기준량(target)과 상태를 함께 보여주도록 상세화.

## 변경 파일 목록

### API (백엔드)
- `page.note.meal/api.py`: AI 분석 결과를 `data/meal_ai_cache/{server_id}/{month}.json`에 캐싱. 식단 데이터 MD5 해시로 변경 감지. `refresh` 파라미터로 강제 재분석 지원. AI 프롬프트를 영양소별 기준량(target)과 상태(status) 포함 포맷으로 변경.

### 프론트엔드 (UI)
- `page.note.meal/view.ts`: `buildNutrientList()`에서 새 포맷(object with percent/target/status) 및 기존 포맷(숫자) 모두 호환. `refreshAiAnalysis()` 함수 추가.
- `page.note.meal/view.pug`: 영양소 항목에 기준량 표시 추가. 재분석 버튼(🔄) 추가. 충족률 색상 분류(충족=파랑, 부족=주황).
- `page.note.meal/view.scss`: `.ns-section-title-row`, `.ns-refresh-btn`, `.ns-nutrient-info`, `.ns-nutrient-target`, `.ns-deficient-target`, `.pct-sufficient/.pct-deficient` 스타일 추가.
