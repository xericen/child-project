# 로그인 후 역할별 리다이렉트 분기 구현

- **ID**: 006
- **날짜**: 2026-03-09
- **유형**: 기능 추가

## 작업 요약
로그인 API에서 role과 childcheck_done 플래그를 반환하도록 수정. 부모(parent) 역할이고 childcheck 미완료 시 /childcheck로, 그 외에는 /note로 리다이렉트. children 테이블에서 user_id로 childcheck 완료 여부 확인.

## 변경 파일 목록
- `src/app/page.main/api.py`: Children 모델 import, login()에서 childcheck_done 확인 및 role/childcheck_done 반환
- `src/app/page.main/view.ts`: onLogin()에서 role/childcheck_done 분기 리다이렉트 구현
