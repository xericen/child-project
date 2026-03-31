# Childcheck 페이지 생성 (부모 전용, 1회성)

- **ID**: 007
- **날짜**: 2026-03-09
- **유형**: 기능 추가

## 작업 요약
부모 역할 사용자가 최초 로그인 후 자녀 정보(이름, 생년월일, 쌍둥이 여부)와 알레르기 정보(계란/우유/땅콩/기타, 중증 여부, 대체식 필요 여부)를 입력하는 2단계 childcheck 페이지 생성.

## 변경 파일 목록
- `src/app/page.childcheck/app.json`: 신규 앱 생성 (viewuri: /childcheck, layout: layout.navbar, controller: base)
- `src/app/page.childcheck/view.ts`: 2단계 폼 로직 (Step1: 자녀정보 확인, Step2: 알레르기 체크)
- `src/app/page.childcheck/view.pug`: 2단계 UI 템플릿
- `src/app/page.childcheck/view.scss`: 디자인 스타일 (보라색 테마, 둥근 카드)
- `src/app/page.childcheck/api.py`: get_child_info(), save_childcheck() 함수
