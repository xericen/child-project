# 전화번호·문의하기·인증확인 기능 일괄 구현

- **ID**: 002
- **날짜**: 2026-03-13
- **유형**: 기능 추가 / 버그 수정

## 작업 요약
FN-20260313-0003 작업 4건 일괄 수행: 원장 회원가입 전화번호 추가, 부모 문의하기(연락처) 페이지, 전 역할 회원정보 전화번호 편집, 회원가입 인증확인 버튼 복구.

## 변경 파일 목록

### Task 1: 원장 회원가입 전화번호
- `src/app/page.server.create/view.pug` — 전화번호 입력 필드 추가 (원장이름 아래)
- `src/app/page.server.create/view.ts` — phone 프로퍼티 및 sendCode 파라미터 추가
- `src/app/page.server.create/api.py` — phone 세션 저장, Users.create 시 phone 포함

### Task 2: 부모 문의하기 연락처 페이지
- `src/app/component.header/view.pug` — 📞 문의하기 메뉴 항목 추가 (부모 전용)
- `src/app/component.header/view.ts` — role 프로퍼티, loadRole(), goContact() 추가
- `src/app/component.header/api.py` — get_role() 엔드포인트 추가
- `src/app/page.contact/` — 신규 페이지 생성 (api.py, view.ts, view.pug, view.scss)
  - api.py: 원장(Servers.director_id → Users) + 담당교사(class_name 매칭) 연락처 조회
  - view.pug: 연락처 카드 UI (전화 걸기 링크 포함)
  - view.scss: 프로젝트 디자인 테마 적용 (#5b6ef5 퍼플)

### Task 3: 회원정보 전화번호 편집
- `src/app/page.myinfo/view.pug` — 이름/전화번호 필드 추가 (전 역할 표시, 편집 가능)
- `src/app/page.myinfo/view.ts` — nickname, phone 프로퍼티 및 저장 로직 추가
- `src/app/page.myinfo/api.py` — Users 테이블 nickname/phone 읽기·쓰기 추가

### Task 4: 인증확인 버튼 복구
- `src/app/page.signup/view.pug` — step-3에 인증확인 버튼 및 이전 버튼 .btn-row 추가
