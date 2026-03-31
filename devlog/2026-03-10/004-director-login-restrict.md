# 원장 로그인 admin/admin만 허용 + 승인 체크

- **ID**: 004
- **날짜**: 2026-03-10
- **유형**: 기능 수정

## 작업 요약
로그인 API에서 원장(director) 계정은 email=admin, password=admin만 허용. 다른 director 계정은 로그인 불가. 교사/부모는 approved=True인 경우만 로그인 가능.

## 변경 파일 목록
- `src/app/page.main/api.py`: login() 함수에 admin/admin 우선 분기, director 차단, approved 체크 추가
- DB: admin 계정 approved=1으로 업데이트
