# 저녁 추천 시 식단표 kcal/protein 기준 스케일링 적용

- **ID**: 005
- **날짜**: 2026-03-27
- **유형**: 기능 추가

## 작업 요약
저녁 추천 분석에서 kcal뿐 아니라 protein도 식단표 DB 값 기준으로 스케일링 적용. AI 프롬프트에 실제 섭취 영양소와 부족분을 명시하여 저녁 추천 정확도 향상.

## 변경 파일 목록

### page.note.today/api.py
- `_get_today_meals()`: `protein` 필드도 반환하도록 추가
- `recommend_dinner()`: `DAILY_RECOMMENDED` → `DAYCARE_TARGET` 참조 변경
- Stage 2 meals에 `target_protein` 필드 추가
- AI 프롬프트 개선: 실제 섭취량(consumed_text) + 부족분(deficit_text) 포함, 칼로리 부족분 기준 저녁 추천

### page.note.today/view.ts
- `fixGreenAndScaling()`: `totalDbProtein`, `proteinRatio` 변수 추가
- protein에 대해 별도 스케일링 비율 적용 (DB protein / API protein)
- 콘솔 로그에 protein 스케일링 정보 추가
