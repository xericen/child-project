# 식약처 API 병렬 호출 + 디스크 캐시 속도 개선

- **ID**: 009
- **날짜**: 2026-03-27
- **유형**: 기능 개선 (성능)

## 작업 요약
식약처 영양소 API 호출을 순차에서 병렬(ThreadPoolExecutor)로 변경하고, 인메모리 캐시를 디스크(JSON 파일)에도 영속 저장하여 서버 재시작 후에도 캐시가 유지되도록 개선. 저녁 추천(recommend_dinner), 월간 통계(get_stats), AI 분석(get_ai_analysis) 세 곳 모두 적용.

## 변경 파일 목록

### Model
- `src/model/nutrition_api.py`
  - `concurrent.futures.ThreadPoolExecutor` import 추가
  - 디스크 캐시: `_load_disk_cache()`, `_save_disk_cache()` 메서드 추가
  - `search()`: 캐시 10건마다 디스크 저장
  - `search_meal()`: 메뉴별 병렬 검색 (max_workers=8)
  - `clear_cache()`: 디스크 캐시 파일도 삭제

### Backend API
- `src/app/page.note.today/api.py`
  - `recommend_dinner()`: 3끼 식단을 ThreadPoolExecutor로 병렬 검색
- `src/app/page.note.meal/api.py`
  - `get_stats()`: DB에 kcal 없는 날의 끼니를 병렬 검색
  - `get_ai_analysis()`: 월간 전체 끼니를 병렬 검색
