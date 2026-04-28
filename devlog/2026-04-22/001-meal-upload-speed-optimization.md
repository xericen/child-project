# 식단표 업로드 속도 최적화 및 프로그레스바 UX 개선

- **ID**: 001
- **날짜**: 2026-04-22
- **유형**: 성능 개선

## 작업 요약
식단표 HWP 업로드 후 "상세 준비 중" 단계가 1~3분 소요되던 문제를 해결. 업로드 완료 시 백엔드에서 영양 캐시를 일괄 선생성하여 이후 프리패치 시 캐시 히트. 프로그레스바를 지수감쇠(점프) 방식에서 선형 증가 방식으로 변경.

## 변경 파일 목록

### 백엔드 (api.py)
- `project/main/src/app/page.note.meal/api.py`
  - `_prebuild_nutrition_cache()` 함수 추가: 업로드 직후 해당 월 전체 날짜의 MealNutritionCache를 일괄 생성
  - `parse_hwp_meal()`: 캐시 무효화 후 `_prebuild_nutrition_cache()` 호출 추가

### 프론트엔드 (view.ts)
- `project/main/src/app/page.note.meal/view.ts`
  - `startHwpProgress()`: 지수감쇠(remaining * 0.06) → 선형 증가(baseStep = 85/600) 방식으로 변경
  - `_hwpStartTime` 변수 추가
  - 프로그레스 라벨 "서버 처리 중..." → "영양 데이터 분석 중..." 변경
  - 서버 응답 후 단계 전환 타겟 조정 (90→88, 라벨 정리)
