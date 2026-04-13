# 기타 알레르기 월간 Gemini 일괄 분석 + 캐시

- **ID**: 005
- **날짜**: 2026-04-10
- **유형**: 기능 개선

## 작업 요약
기타 알레르기(표준 19종 미해당) 감지를 키워드별 개별 분석에서 월간 일괄 Gemini 분석으로 전환.
- 한 달 전체 식단 음식명을 수집 → Gemini에 1회만 질문 → 결과를 `batch.json`으로 캐시
- "카레라이스"에 "땅콩"이 재료로 포함되는지 같은 재료 수준 분석이 가능해짐
- API 호출 횟수: 키워드 N개 × 개별 호출 → 1회 일괄 호출로 대폭 감소

## 변경 파일 목록

### Backend
- `src/app/page.note.today/api.py`
  - `_extract_all_food_names()`: 신규 - 식단 content에서 모든 음식명 추출
  - `_build_monthly_allergy_cache()`: 신규 - 월간 Gemini 일괄 분석 + 파일 캐시
  - `_get_ingredient_cache()`: 개선 - per-keyword 해시 파일 → batch.json 단일 파일에서 읽기
  - `get_today_menu()`: 19종 미해당 기타 키워드를 필터링하여 월간 캐시 빌드 트리거 추가
