# AI 저녁 추천 3단계 정밀 영양소 분석 고도화

- **ID**: 004
- **날짜**: 2026-03-25
- **유형**: 기능 추가

## 작업 요약
부모용 AI 저녁 추천 기능을 단순 텍스트 응답에서 3단계 구조화된 JSON 분석으로 고도화. Gemini에 구조화된 프롬프트를 전송하여 영양소 수치, 권장량 대비 부족분, 맞춤 저녁 메뉴를 단계별로 제공.

## 변경 파일 목록

### page.note.today/api.py
- `recommend_dinner()`: `gemini.ask()` → `gemini.ask_json()`으로 변경
- 3단계 JSON 구조 프롬프트 설계 (stage1: 영양소 수치, stage2: 권장량 대비, stage3: 저녁 추천)
- 응답 형식: `{analysis: {...}}` 구조화된 데이터로 반환
- `_get_today_meals()` KST 날짜 사용

### page.note.today/view.ts
- 단일 `dinnerRecommendation` 문자열 → `analysis` 구조화 객체로 변경
- `getNutrientLabel()`, `getNutrientUnit()`, `getDeficitPercent()`, `nutrientKeys()` 헬퍼 추가
- `formatMarkdown()` 제거 (더 이상 마크다운 텍스트 미사용)

### page.note.today/view.pug
- 단순 텍스트 표시 → 3단계 카드 UI로 변경
- Stage 1: 식사별 음식 항목 + 영양소 + 총합
- Stage 2: 프로그레스 바 + 권장량 대비 수치
- Stage 3: 추천 메뉴 카드 + 영양소 태그 + 조리 팁

### page.note.today/view.scss
- 3단계 카드 스타일 추가 (`.stage-card`, `.stage-header`, `.stage-num`)
- 영양소 프로그레스 바 (`.deficit-bar-wrap`, `.deficit-bar`)
- 추천 메뉴 카드 (`.recommend-card`, `.nutrient-mini`)
- 조리 팁 박스 (`.tip-box`)
