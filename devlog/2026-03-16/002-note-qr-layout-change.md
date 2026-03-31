# Note 페이지 QR 코드 레이아웃 변경

- **ID**: 002
- **날짜**: 2026-03-16
- **유형**: UI 개선

## 작업 요약
Note 페이지의 QR 코드를 토글 버튼 방식에서 항상 표시되도록 변경. 상단 영역을 flex row로 구성하여 왼쪽에 배지+타이틀+서브타이틀, 오른쪽에 QR 이미지를 배치. 원장 로그인 시 자동으로 QR 코드 로드.

## 변경 파일 목록
### UI
- `src/app/page.note/view.pug`: 토글 버튼 UI 제거, `.top-area` flex row 레이아웃으로 변경 (좌: 텍스트, 우: QR)
- `src/app/page.note/view.ts`: `showQR`/`toggleQR()` 제거, `loadQR()` 메서드 추가하여 원장 시 자동 호출
- `src/app/page.note/view.scss`: QR 토글 관련 스타일 제거, `.top-area`/`.top-left`/`.top-right` 가로 배치 스타일 추가
