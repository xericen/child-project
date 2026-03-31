# navigateByUrl 오류 수정

- **ID**: 006
- **날짜**: 2026-03-30
- **유형**: 버그 수정

## 작업 요약
`goNutritionDashboard()`에서 `service.href()` 사용 시 `Cannot read properties of undefined (reading 'navigateByUrl')` 에러 발생. Angular Router 직접 주입으로 수정.

## 변경 파일 목록
### page.note.meal/view.ts
- `goNutritionDashboard()`: `this.service.href()` → `this.router.navigateByUrl('/note/meal/nutrition')` 변경
