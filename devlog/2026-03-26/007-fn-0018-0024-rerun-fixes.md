# FN-0018~0024 재수행 정정

- **ID**: 007
- **날짜**: 2026-03-26
- **유형**: 버그 수정

## 작업 요약
FN-0018~0024를 다시 점검하며 누락된 정정을 반영했다. 저녁 추천/green 제외 로직이 최신 코드로 반영되도록 클린 빌드를 수행했고, 통계의 3~5세 동적 표시 로직을 제거하여 1~2세만 남겼다. 프로필의 부모 전화번호는 라벨 아래 줄로 내려 표시되도록 레이아웃을 수정했다.

## 변경 파일 목록

### 오늘의 식단
- `src/model/nutrition_api.py`: green 마커 제거 로직 유지 확인
- `src/app/page.note.today/api.py`: 점심 kcal 스케일링 및 green 제외 로직 최신 상태 확인

### 식단 통계
- `src/app/page.note.meal/api.py`: 3~5세 동적 표시 제거, `AGE_NUTRITION`을 1~2세만 유지

### 프로필
- `src/app/page.note.profile/view.pug`: 부모 전화번호 행을 라벨 아래 값이 오도록 `.phone-row`, `.phone-value` 구조 적용
- `src/app/page.note.profile/view.scss`: 전화번호 행 세로 배치 스타일 적용

### 빌드
- 클린 빌드 수행 (`clean: true`)로 최신 프론트/백엔드 변경 강제 반영