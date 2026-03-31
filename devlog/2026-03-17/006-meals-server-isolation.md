# 식단 데이터 서버(방)별 분리

- **ID**: 006
- **날짜**: 2026-03-17
- **유형**: 버그 수정

## 작업 요약
Meals 테이블에 server_id 컬럼을 추가하여 서버(어린이집)별 식단 데이터를 완전히 격리. 1서버에 올린 식단이 2서버에 보이는 문제 해결.

## 변경 파일 목록

### DB Model
- `src/model/db/childcheck/meals.py`: server_id 필드 추가 (IntegerField, index=True)

### API 수정 (server_id 기반 필터링 적용)
- `src/app/page.note.meal/api.py`: 전체 Meals CRUD에 server_id 필터 적용, meal_files 경로를 서버별로 분리 (`data/meal_files/{server_id}/`), notify_parents를 서버 소속 학부모만 대상으로 변경, Children/ChildAllergies 조회를 서버 소속 아동으로 한정
- `src/app/page.note.today/api.py`: 오늘의 식단 조회, 알레르기 경고, AI 추천 모두 server_id 기반으로 변경
- `src/app/page.note.activity/api.py`: 주간 식단 조회에 server_id 필터 적용

### DB 스키마
- `ALTER TABLE meals ADD COLUMN server_id INT NOT NULL DEFAULT 0 AFTER id` 실행 완료
