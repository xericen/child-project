# 자동 로그인 로그아웃 수정 + 텍스트 오버플로 수정

- **ID**: 023
- **날짜**: 2026-03-17
- **유형**: 버그 수정

## 작업 요약
자동 로그인 활성화 상태에서 로그아웃 시 localStorage의 `child_auto_login`이 삭제되지 않아 즉시 재로그인되는 문제 수정. 설치 안내 단계 텍스트가 칸 밖으로 나오는 오버플로 문제도 함께 수정.

## 변경 파일 목록
### component.header
- **view.ts**: `logout()` 메서드에 `localStorage.removeItem('child_auto_login')` 추가
