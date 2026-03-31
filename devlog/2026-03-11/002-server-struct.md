# 서버 비즈니스 로직 Model/Struct 구현

- **ID**: 002
- **날짜**: 2026-03-11
- **유형**: 기능 추가

## 작업 요약
서버 생성·참여 비즈니스 로직을 Struct 패턴으로 구현. 8자리 영숫자 고유 코드 생성, 서버 생성, 코드로 서버 조회, 멤버 참여 기능 포함.

## 변경 파일 목록
### Model
- `src/model/struct/server.py` — Server Sub-Struct (create, find_by_code, join 메서드)
- `src/model/struct.py` — server property 추가
