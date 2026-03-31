# 알레르기 해제 후 대체식(green) 칼로리 0 수정

- **ID**: 012
- **날짜**: 2026-03-27
- **유형**: 버그 수정

## 작업 요약
HWP 파싱 시 `{{green:메뉴명}}`으로 DB에 영구 저장된 대체식이 영양 분석에서 무조건 제외되어 칼로리 0으로 표시되는 문제 수정. green 아이템을 영양 검색에 포함하되 `is_substitute` 플래그로 구분. 합산 시 대체식은 제외하여 중복 합산 방지.

## 변경 파일 목록
- `src/model/nutrition_api.py`: search_meal() — green 내부 텍스트도 검색하되 is_substitute 플래그 부여
- `src/app/page.note.today/view.ts`: fixGreenAndScaling — green 아이템 filter 제거 대신 합산에서만 제외
- `src/app/page.note.today/api.py`: recommend_dinner — green 전처리 제거 (search_meal이 처리), is_substitute 플래그 전달
