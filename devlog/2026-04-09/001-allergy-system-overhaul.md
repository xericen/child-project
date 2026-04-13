# 알레르기 시스템 전면 개편 (19종 체크 + 재료 AI 캐시 + 프로필 검색)

- **ID**: 001
- **날짜**: 2026-04-09
- **유형**: 기능 추가

## 작업 요약
childcheck 알레르기 UI를 3종(계란/우유/땅콩)에서 19종 표준 알레르기 전체 선택으로 개편하고, 기타 알레르기(감자 등 비표준) 검출을 위한 AI 재료 배치 분석 + 캐시 시스템을 구축. 교사/원장 프로필 페이지에 아이 검색 기능 추가.

## 변경 파일 목록

### childcheck 알레르기 UI 개편
- `src/app/page.childcheck/view.ts` — 19종 standardAllergies 배열, 3스텝(자녀정보→19종→기타/중증) 전환
- `src/app/page.childcheck/view.pug` — 3스텝 UI, 19종 그리드 카드, 기타 알레르기 입력 분리
- `src/app/page.childcheck/view.scss` — allergy-grid 2열 카드 스타일, form-hint
- `src/app/page.childcheck/api.py` — save_childcheck 시 기타 알레르기 AI 배치 분석 → allergy_ingredient_cache 저장

### 알레르기 검출 로직 개선
- `src/app/page.note.today/api.py` — _keyword_in_content에 AI 재료 캐시 조회 추가, _get_ingredient_cache 함수
- `src/app/page.note.meal/api.py` — 동일한 _keyword_in_content 개선 적용

### 프로필 검색 기능
- `src/app/page.note.profile/view.ts` — searchText, filteredClasses, filteredChildren, applyFilter(), onSearch()
- `src/app/page.note.profile/view.pug` — 검색 입력란 추가, filteredClasses/filteredChildren으로 표시
- `src/app/page.note.profile/view.scss` — search-box, search-input 스타일
