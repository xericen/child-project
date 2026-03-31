# 식단 DB에 단백질(protein) 필드 추가 및 HWP 파서 수정

- **ID**: 004
- **날짜**: 2026-03-27
- **유형**: 기능 추가

## 작업 요약
meals 테이블에 `protein` 컬럼을 추가하고, HWP 식단표 파서에서 단백질 행을 파싱하여 DB에 저장하도록 수정.

## 변경 파일 목록

### model/db/childcheck/meals.py
- `protein = pw.FloatField(null=True)` 필드 추가

### DB 스키마
- `ALTER TABLE meals ADD COLUMN protein FLOAT NULL AFTER kcal` 실행 완료

### page.note.meal/api.py
- HWP 파서: `is_protein` 플래그 추가, '단백질' 행 감지 시 `daily_protein` dict에 값 저장
- HWP 초기 저장(`Meals.create`): `protein=meal_protein` 파라미터 추가
- HWP 업데이트(`Meals.update`): `protein=meal_protein` 파라미터 추가
- `save_meal()`: `protein` 쿼리 파라미터 수신 및 저장
- `update_meal()`: `protein` 쿼리 파라미터 수신 및 저장
