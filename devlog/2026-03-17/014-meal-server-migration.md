# 식단 서버(방) 분리 — 기존 데이터 마이그레이션

- **ID**: 014
- **날짜**: 2026-03-17
- **유형**: 버그 수정 / 데이터 마이그레이션

## 작업 요약
이전 작업(FN-0001)에서 코드에 server_id 필터링을 적용했으나, 기존 75건의 식단 데이터가 server_id=0으로 남아있어 어느 서버에서도 식단이 보이지 않거나 양쪽에 다 보이는 문제 발생. created_by(user_id=49)의 소속 서버(server_id=6, 시즌 어린이집)를 추적하여 일괄 마이그레이션. 파일 저장소도 서버별 디렉토리로 이동.

## 변경 내용

### DB 마이그레이션
- `UPDATE meals SET server_id = 6 WHERE server_id = 0` — 75건 마이그레이션

### 파일 이동
- `data/meal_files/*.hwp` + `meta.json` → `data/meal_files/6/` 디렉토리로 이동
- 기존: 서버 구분 없이 `data/meal_files/`에 저장
- 이후: `data/meal_files/{server_id}/` 구조로 서버별 분리

### 코드 검증
- `_get_server_id()`: 세션 미설정 시 401 반환 (이미 방어 처리됨)
- `parse_hwp_meal()`: `_get_server_id()`로 server_id 추출 후 `Meals.create(server_id=server_id)` 정상 적용 확인
