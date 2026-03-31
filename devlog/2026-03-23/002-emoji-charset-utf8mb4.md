# 사진 댓글 이모지 깨짐(???) 수정

- **ID**: 002
- **날짜**: 2026-03-23
- **유형**: 버그 수정

## 작업 요약
사진 댓글에서 이모지가 `???`로 깨지는 문제를 수정했다. DB charset이 `utf8`(3바이트)로 설정되어 4바이트 이모지를 저장할 수 없었다. `config/database.py`의 두 DB charset을 `utf8mb4`로 변경하고, MySQL에서 관련 테이블을 `utf8mb4_unicode_ci`로 ALTER했다.

## 변경 파일 목록

### Config
- `config/database.py`: `childcheck`, `login_db` 두 DB의 charset을 `utf8` → `utf8mb4`로 변경

### DB 마이그레이션
- MySQL: `childcheck`, `login_db` 모든 테이블을 `utf8mb4_unicode_ci`로 ALTER TABLE 실행
