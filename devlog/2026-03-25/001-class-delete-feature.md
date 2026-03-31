# 원장 프로필 - 반 전체 삭제 기능 추가

- **ID**: 001
- **날짜**: 2026-03-25
- **유형**: 기능 추가

## 작업 요약
원장(director) 프로필 페이지에서 반(class) 전체를 삭제할 수 있는 기능을 추가했다. 반 이름 옆에 X 버튼을 배치하고, 클릭 시 해당 반의 교사, 학생(자녀), 학부모 데이터를 일괄 삭제한다.

## 변경 파일 목록

### API (백엔드)
- `src/app/page.note.profile/api.py`: `delete_class()` 함수 추가 — class_name 기준으로 해당 반의 교사(Users+ServerMembers), 학부모(Users+ServerMembers), 자녀(Children+ChildAllergies) 일괄 삭제

### 프론트엔드
- `src/app/page.note.profile/view.ts`: `deleteClass(className)` 메서드 추가 — confirm 다이얼로그 후 API 호출, 데이터 새로고침
- `src/app/page.note.profile/view.pug`: 원장 뷰의 반 제목 행에 `.section-title-row` 래퍼 추가, X 삭제 버튼(`.btn-delete-class`) 배치
- `src/app/page.note.profile/view.scss`: `.section-title-row`, `.btn-delete-class` 스타일 추가, 기존 `.section-title`에서 margin/border 분리
