# 통계 영양소 충족률 캐싱 안정화 (FN-0005 + FN-0008)

- **ID**: 005
- **날짜**: 2026-03-25
- **유형**: 버그 수정

## 작업 요약
통계 페이지 진입 시마다 영양소 충족률이 변하던 문제 수정. AI 분석 캐시를 식단 데이터 해시 기반 무효화에서 명시적 refresh 기반으로 변경하여 일관된 수치 제공.

## 변경 파일 목록

### page.note.meal/api.py
- `get_ai_analysis()`: 캐시가 존재하면 항상 반환 (data_hash 불일치 시에도)
- `data_changed` 플래그 추가: 식단 데이터가 변경되었음을 프론트엔드에 알림
- `cached_at` 응답에 포함: 캐시 생성 시간 표시

### page.note.meal/view.ts
- `aiCachedAt`, `aiDataChanged` 변수 추가
- `loadAiAnalysis()`: 응답에서 `cached_at`, `data_changed` 읽기

### page.note.meal/view.pug
- 영양소 충족률 섹션에 "분석일: YYYY-MM-DD HH:MM" 표시
- 식단 변경 시 "· 식단 변경됨" 경고 표시

### page.note.meal/view.scss
- `.ns-cache-info`, `.ns-data-changed` 스타일 추가
