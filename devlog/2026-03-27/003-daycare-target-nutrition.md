# 하루 권장량 대비 영양소 비교 기능 개선

- **ID**: 003
- **날짜**: 2026-03-27
- **유형**: 기능 추가

## 작업 요약
Stage 2 분석의 비교 기준을 하루 전체 기준(900kcal)에서 어린이집 제공분 목표치(420kcal, 점심+간식2회)로 변경. 각 영양소별 "부족/초과/적정" 상태를 계산하고 시각적으로 구분하는 UI 추가.

## 변경 파일 목록

### page.note.today/api.py
- `DAILY_RECOMMENDED` → `DAYCARE_TARGET`으로 변경 (420kcal/20g protein/14g fat/63g carbs/450mg calcium/3mg iron)
- Stage 2 응답에 `surplus`, `status` 필드 추가 (부족/초과/적정 판정, 10% 허용 범위)

### page.note.today/view.ts
- `fixGreenAndScaling()`: deficit 재계산 시 surplus/status도 함께 계산
- `getNutrientStatus()` 헬퍼 함수 추가

### page.note.today/view.pug
- Stage 2 제목: "하루 권장량 대비" → "어린이집 제공 목표 대비"
- 각 행에 상태별 CSS 클래스 적용 (status-low/status-over/status-ok)
- 상태 배지 표시: 부족(빨강), 초과(+수치, 주황), 적정(초록)

### page.note.today/view.scss
- `.status-badge`, `.badge-low`, `.badge-over`, `.badge-ok` 스타일 추가
- `.deficit-row` 상태별 라벨 색상 지정
