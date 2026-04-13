# 영양분석 칼로리/단백질 DB값 직접 사용 + Ca/Fe API 비율보정

- **ID**: 004
- **날짜**: 2026-04-10
- **유형**: 기능 개선

## 작업 요약
영양분석 파이프라인(`_ai_analyze_all_meals`)을 3단계→2단계로 간소화.
- 열량/단백질: 식단표 DB(`kcal`, `protein`)값을 total에 직접 사용 (API 스케일링 오차 제거)
- 칼슘/철분: 식약처 API에서 가져온 값에 열량비율(`db_kcal/api_kcal`) 보정 적용 (기존 AI 추정 제거)
- Phase 3(Gemini AI 칼슘/철분 추정) 완전 제거 → API 호출 1회 절약

## 변경 파일 목록

### Backend
- `src/app/page.note.today/api.py`
  - `_ai_analyze_all_meals()`: 3단계→2단계 파이프라인
    - Phase 1: calcium/iron도 식약처 API에서 가져오도록 변경 (기존 0.0 고정 제거)
    - Phase 2: calcium/iron에도 cal_ratio 스케일링 적용
    - Phase 3(AI 칼슘/철분 추정): 완전 제거
    - 결과 조립: total calories/protein을 DB값으로 강제 고정
  - `_ai_estimate_calcium_iron()`: 더 이상 호출되지 않음 (함수는 잔존)
