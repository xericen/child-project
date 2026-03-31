# DB 스키마 변경 — users 테이블 컬럼 추가

- **ID**: 001
- **날짜**: 2026-03-10
- **유형**: 설정 변경

## 작업 요약
users 테이블에 `class_name`(교사 반 정보)과 `approved`(가입 승인 여부) 컬럼을 추가했다. DB Model과 실제 테이블 모두 반영.

## 변경 파일 목록
- `src/model/db/login_db/users.py`: class_name(VARCHAR 50, nullable), approved(BOOLEAN, default 0) 컬럼 추가
- DB: ALTER TABLE users ADD COLUMN 2건 실행
