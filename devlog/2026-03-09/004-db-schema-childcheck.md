# DB 스키마 보완 및 childcheck namespace 추가

- **ID**: 004
- **날짜**: 2026-03-09
- **유형**: 설정 변경

## 작업 요약
childcheck DB namespace를 config/database.py에 추가하고, users 테이블에 child_name 컬럼, children 테이블에 user_id 컬럼을 ALTER TABLE로 추가. Peewee 모델 파일도 동기화.

## 변경 파일 목록
- `config/database.py`: childcheck namespace 추가
- `src/model/db/login_db/users.py`: child_name 필드 추가
- `src/model/db/childcheck/children.py`: user_id 필드 추가
- MySQL: ALTER TABLE users ADD child_name, ALTER TABLE children ADD user_id
