# AI 모델 업데이트 + 알레르기 텍스트 매칭 전환

- **ID**: 030
- **날짜**: 2026-03-17
- **유형**: 버그 수정

## 작업 요약
1. AI 모델을 deprecated된 `gemini-2.0-flash-lite`에서 `gemini-2.5-flash`로 변경하여 404 에러 해결.
2. 기타 알레르기 매칭 로직을 카테고리 번호 기반에서 실제 식단 텍스트 키워드 검색으로 전환.
   - 식단에 없는 식품(예: 굴)에 대한 거짓 양성 알림 제거.
   - 복합어 처리를 위한 KEYWORD_ALIASES 추가 (돼지고기→돼지, 닭고기→닭 등).

## 변경 파일 목록

### Config
- `config/ai.py`: model을 `gemini-2.0-flash-lite` → `gemini-2.5-flash`로 변경

### App API
- `src/app/component.header/api.py`:
  - `KEYWORD_ALIASES` dict 추가 (고기류 복합어 확장)
  - `_keyword_in_content()` 헬퍼 함수 추가 (키워드 + alias 검색)
  - `get_weekly_allergy()` 기타 알레르기: `cat_nums & all_meal_numbers` 카테고리 번호 매칭 제거
  - `get_weekly_allergy()` 기타 알레르기: `_keyword_in_content(keyword, all_meal_content)` 텍스트 검색으로 전환

## 검증 결과
- 이전: 7개 알림 (굴 2건 포함)
- 수정 후: 5개 알림 (굴 알레르기 2건 정상 제거)
- 돼지고기: "돼지갈비찜"에서 "돼지" 매칭 → 알림 유지 ✅
- 키위: "키위\n두유"에서 매칭 → 알림 유지 ✅
- 닭고기: "닭고기죽"에서 매칭 → 알림 유지 ✅
