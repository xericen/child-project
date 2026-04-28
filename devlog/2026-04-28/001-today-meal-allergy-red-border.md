# 오늘의 식단 알레르기 표시를 빨간 테두리 방식으로 변경

- **ID**: 001
- **날짜**: 2026-04-28
- **유형**: 기능 추가

## 작업 요약
부모 로그인 시 오늘의 식단(page.note.today)에서 알레르기 해당 메뉴 카드에 식단표(page.note.meal)와 동일한 빨간 테두리+배경색 강조를 적용했다. 기존 ⚠️ 텍스트 경고는 유지하여 빨간 테두리와 경고 텍스트를 병행 표시한다.

## 변경 파일 목록

### view.pug
- 오전간식/점심/오후간식 `.tl-block`에 `[class.allergy-danger]` 바인딩 추가
- 분석 결과(page 0) 타임라인 `.tl-block`에도 동일 바인딩 추가

### view.scss
- `.tl-block.allergy-danger .tl-card` 스타일 추가 (`border-color: #e74c3c; background: #fff5f5;`)
- 식단표 페이지와 동일한 색상 코드 사용
