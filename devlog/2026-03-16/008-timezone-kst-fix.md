# created_at 타임존 KST 보정

- **ID**: 008
- **날짜**: 2026-03-16
- **유형**: 버그 수정

## 작업 요약
MySQL 서버와 앱 서버 모두 UTC로 동작하여 `CURRENT_TIMESTAMP` 기본값이 한국시간(KST) 대비 -9시간으로 저장되던 문제 수정. `config/database.py`의 login_db, childcheck 양쪽 커넥션에 `init_command = "SET time_zone='+09:00'"` 추가하고, ORM 커넥션 코드(`portal/season/model/dbbase/mysql.py`)의 허용 키 목록에 `init_command`를 추가하여 세션 타임존이 KST로 설정되도록 수정.

## 변경 파일 목록
### Config
- `config/database.py`: login_db, childcheck 양쪽에 `init_command = "SET time_zone='+09:00'"` 추가

### ORM
- `src/portal/season/model/dbbase/mysql.py`: opts 허용 키에 `init_command` 추가
