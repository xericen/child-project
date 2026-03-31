# 영양소 계산·알레르기·연령대·텍스트 수정

- **ID**: 006
- **날짜**: 2026-03-26
- **유형**: 버그 수정 + 기능 추가

## 작업 요약
FN-0018~0024 일괄 수행. nutrition_api green 마커 제외 방식을 줄 스킵→아이템 단위 제거로 변경. 알레르기 경고를 교사/원장에게도 확장. 3~5세 연령대 동적 표시 로직 추가. 프로필 카드 텍스트 잘림 수정.

## 변경 파일 목록

### Model
- `src/model/nutrition_api.py`: search_meal()에서 GREEN_PATTERN.search→줄스킵을 GREEN_PATTERN.sub→마커제거로 변경 (같은 줄에 정상 메뉴와 대체제가 섞인 경우 정상 메뉴 보존)

### 오늘의 식단 (page.note.today)
- `api.py`: get_today_menu() 알레르기 경고를 parent만→전 역할(teacher/director 포함)로 확장. teacher/director는 서버 내 전체 자녀 알레르기를 집계하여 매칭.

### 식단 통계 (page.note.meal)
- `api.py`: AGE_NUTRITION→AGE_NUTRITION_ALL로 리네이밍, 3~5세 영양 기준 추가(kcal:550, protein:25, calcium:400). get_stats()에서 서버 내 3세 이상 자녀 존재 시 3~5세 항목 동적 포함. get_parent_stats()의 AGE_NUTRITION 참조 수정.

### 프로필 (page.note.profile)
- `view.scss`: .card-name, .card-sub에서 white-space:nowrap/overflow:hidden/text-overflow:ellipsis 제거 → word-break:break-all 적용
