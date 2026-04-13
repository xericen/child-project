# 저녁 추천 성능 개선 + 알레르기 감지 + UI 개선

- **ID**: 003
- **날짜**: 2026-04-10
- **유형**: 기능 추가

## 작업 요약
저녁 추천 영양분석 결과를 DB에 캐시하여 반복 호출 시 즉시 로드되도록 개선. 기타 알레르기 키워드 미매칭 시 "확인 필요" 플래그 추가. 네비게이션 버튼 크기 축소 및 저녁 추천 페이지에 칼로리 진행률 링 차트 추가.

## 변경 파일 목록

### DB 모델 (신규)
- `src/model/db/childcheck/meal_nutrition_cache.py`: 식단 영양분석 캐시 테이블 (server_id + meal_date + age_group unique)

### 백엔드
- `src/app/page.note.today/api.py`:
  - MealNutritionCache 모델 import 추가
  - `_keyword_in_content()`: 반환값을 `(matched, confidence)` 튜플로 변경
  - 알레르기 매칭: 미매칭 키워드에 "(확인 필요)" 접미사 추가
  - `_recommend_dinner_impl()`: 캐시 확인 → 분석 → 캐시 저장 로직 추가

### 프론트엔드
- `view.ts`: `getDailyCaloriePercent()`, `getDailyCalorieDeficit()`, `getCalorieRingOffset()`, `getCalorieRingCircumference()` 메서드 추가
- `view.pug`: 저녁 추천 페이지에 SVG 링 차트 진행률 바 + 부족 칼로리 텍스트 추가
- `view.scss`: 네비게이션 버튼 크기 축소 (padding 7px→5px, font 0.82rem→0.72rem), 칼로리 진행률 링 스타일 추가
