# 어린이집 서버 DB 설계 및 생성

- **ID**: 001
- **날짜**: 2026-03-11
- **유형**: 기능 추가

## 작업 요약
어린이집(서버) 관리를 위한 `servers`, `server_members` 테이블을 MySQL `login_db`에 설계·생성하고, Peewee ORM 모델 파일을 작성했다.

## 변경 파일 목록
### DB Model
- `src/model/db/login_db/servers.py` — servers 테이블 Peewee 모델 (server_code, name, director_name, director_id)
- `src/model/db/login_db/server_members.py` — server_members 테이블 Peewee 모델 (server_id, user_id, role)

### MySQL
- `login_db.servers` 테이블 CREATE
- `login_db.server_members` 테이블 CREATE
