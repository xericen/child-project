# 오전간식/점심/오후간식 3분류 변경

- **ID**: 002
- **날짜**: 2026-03-12
- **유형**: 기능 수정

## 작업 요약
식단 종류를 기존 "간식/점심" 2개에서 "오전간식/점심/오후간식" 3개로 변경. 오늘의 식단 페이지, 식단표 페이지(등록 폼, 목록 표시, API) 모두 반영.

## 변경 파일 목록
- `src/app/page.note.today/view.pug`: 카드 3개(오전간식, 점심, 오후간식)
- `src/app/page.note.today/view.ts`: morningSnack, lunchMenu, afternoonSnack 변수
- `src/app/page.note.today/api.py`: meal_type 3개 분기 매핑
- `src/app/page.note.meal/view.pug`: select 옵션 3개 + getMealIcon 사용
- `src/app/page.note.meal/view.ts`: getMealIcon 메서드 추가
- `src/app/page.note.meal/api.py`: type_labels 딕셔너리로 알림 메시지 분기
