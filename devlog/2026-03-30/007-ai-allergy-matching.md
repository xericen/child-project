# AI 기반 알레르기 매칭 강화 — 기타 알레르기 + 음식-알레르기 성분 분석

- **ID**: 007
- **날짜**: 2026-03-30
- **유형**: 기능 추가

## 작업 요약
기타 알레르기(돼지고기, 햄 등)가 표준 19종에 매핑되지 않는 문제 해결. AI 기반 음식-알레르기 성분 분석 및 비표준 알레르기 키워드 매핑 기능 추가. KEYWORD_ALIASES 대폭 확장.

## 변경 파일 목록
### page.note.meal/api.py
- `_ai_analyze_dish_allergies()` 신규 — AI로 각 음식의 알레르기 성분 분석
- `_ai_map_other_allergy()` 신규 — 비표준 알레르기 키워드를 19종에 매핑
- `save_meal()` / `update_meal()` — AI 분석 통합
- `_get_child_allergy_numbers()` — AI fallback 추가
- `get_daily()` — dish_allergies 기반 per-dish 알레르기 매칭
- `get_parent_stats()` — AI fallback 알레르기 번호 수집
- `KEYWORD_ALIASES` — 돼지고기(15개), 닭고기(6개), 쇠고기(8개) 등 대폭 확장

### page.note.today/api.py
- `_ai_map_other_allergy()`, `KEYWORD_ALIASES`, `_keyword_in_content()` 동기화
- `_get_today_meals()` — dish_allergies 반환
- `get_today_menu()` — 3단계 알레르기 매칭 (dish_allergies → 번호교집합 → 키워드)
