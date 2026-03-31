# 회원가입 역할에서 원장 제거 + 교사 반 입력 추가

- **ID**: 002
- **날짜**: 2026-03-10
- **유형**: 기능 추가

## 작업 요약
회원가입 역할 선택에서 원장(director) 옵션을 제거하고, 교사 선택 시 담당 반(class_name) 입력 필드를 추가했다. 백엔드에서도 교사 class_name을 DB에 저장하도록 수정.

## 변경 파일 목록
- `src/app/page.signup/view.pug`: 원장 옵션 삭제, 교사 반 입력 필드 추가, 쿨다운 UI 제거
- `src/app/page.signup/view.ts`: className 변수 추가, isStep1Complete에 교사 조건 추가, 쿨다운 로직 제거
- `src/app/page.signup/api.py`: class_name 파라미터 수신 및 교사 저장, approved=False 기본값
