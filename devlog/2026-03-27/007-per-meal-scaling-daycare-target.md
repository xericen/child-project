# per-meal 스케일링 + DAYCARE_TARGET 프론트 강제 적용

- **ID**: 007
- **날짜**: 2026-03-27
- **유형**: 버그 수정 / 기능 개선

## 작업 요약
globalRatio(전체 합산 비율) → per-meal ratio(끼니별 비율)로 스케일링 방식 변경. Stage 1 총 섭취량과 Stage 2 칼로리 불일치 해결. DAYCARE_TARGET(420kcal 등)을 프론트에서 강제 적용하여 서버 캐시 무관.

## 변경 파일 목록

### page.note.today/view.ts
- `fixGreenAndScaling()`: globalRatio 삭제 → 끼니별 `kcalRatio`/`pRatio` 계산으로 변경
- DB kcal 없는 끼니(오전간식, 오후간식)는 ratio=1.0 (API 원본 유지)
- DB kcal 있는 끼니(점심)만 `target_kcal / apiCal` 비율 적용
- `DAYCARE_TARGET` 하드코딩으로 `stage2.recommended` 강제 설정
