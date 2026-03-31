# 가입 승인 시 아이 프로필(children) 자동 생성

- **ID**: 001
- **날짜**: 2026-03-20
- **유형**: 버그 수정

## 작업 요약
원장이 부모 가입을 승인할 때 `children` 테이블에 레코드가 자동 생성되지 않아 프로필 페이지에 아이 정보가 누락되는 문제를 수정했다. 또한 미승인 사용자가 프로필 페이지에 노출되던 문제도 함께 해결했다.

## 변경 파일 목록

### 백엔드
- `src/app/page.note.approve/api.py`
  - `approve_user()`: 승인 후 부모(role='parent')인 경우 `users.child_name`, `users.birth_date` 정보로 `children` 레코드 자동 생성
  - 기존 children 레코드가 있으면 중복 생성하지 않음 (childcheck에서 이미 등록한 경우)

- `src/app/page.note.profile/api.py`
  - `get_profile_data()`: 부모 조회 시 `Users.approved == True` 조건 추가 (교사/원장 쿼리 모두)
  - 미승인 사용자는 더 이상 프로필 페이지에 노출되지 않음
