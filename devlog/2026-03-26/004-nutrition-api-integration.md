# 식약처 영양성분 API 연동

- **ID**: 004
- **날짜**: 2026-03-26
- **유형**: 기능 추가

## 작업 요약
식약처 식품영양성분DB(FoodNtrCpntDbInfo02) API를 연동하는 영양소 조회 모델(`nutrition_api.py`) 구축. 저녁 추천(recommend_dinner)에서 식약처 실측 데이터 기반으로 Gemini 프롬프트 강화. 통계 페이지(get_stats/get_ai_analysis)에서 API 기반 일별 칼로리 보완 및 월간 영양소 실측 데이터를 AI 분석 프롬프트에 포함.

## 변경 파일 목록
### 모델 (신규)
- `src/model/nutrition_api.py`: 식약처 API 클라이언트 모델 (검색, 캐싱, 매칭 스코어링, 기본 식재료 테이블, search_meal 합산 기능)

### API (수정)
- `src/app/page.note.today/api.py`: recommend_dinner() - 식약처 API 실측 데이터를 Gemini 프롬프트에 포함, nutrition_data 응답 추가
- `src/app/page.note.meal/api.py`: get_stats() - API 기반 일별 칼로리 보완, get_ai_analysis() - 월간 식약처 실측 평균 데이터를 AI 프롬프트에 포함
