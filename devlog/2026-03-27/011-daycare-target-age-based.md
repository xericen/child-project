# DAYCARE_TARGET 연령별 영양 기준 변경

- **ID**: 011
- **날짜**: 2026-03-27
- **유형**: 기능 개선

## 작업 요약
1~2세 값 수정(protein 20→9.3, calcium 450→210 등) + 3~5세(640kcal) 신규 추가. 자녀 나이(Children.birthdate)에 따라 자동 선택. 4개 파일 동시 수정.

## 변경 파일 목록
- `src/app/page.note.today/api.py`: DAYCARE_TARGETS 딕셔너리 + _get_daycare_target() 함수 추가
- `src/app/page.note.today/view.ts`: 프론트 DAYCARE_TARGETS 연령별, childAge 기반 선택
- `src/app/page.note.meal/api.py`: AGE_NUTRITION에 3~5세 추가, get_ai_analysis에 age 파라미터 수신
- `src/app/page.note.meal/view.ts`: loadAiAnalysis에서 selectedAge 전달
