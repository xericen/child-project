# 아이 개인 사진 기능

- **ID**: 014
- **날짜**: 2026-03-11
- **유형**: 기능 추가

## 작업 요약
교사가 "아이사진" 카테고리 선택 시 본인 반 아이 목록을 표시하고, 특정 아이를 선택하면 해당 아이 전용 사진 갤러리로 진입하여 사진을 올릴 수 있도록 구현. 부모는 "아이사진" 클릭 시 자기 아이의 사진만 바로 표시. 업로드 시 target_user_id로 대상 아이(부모)를 지정하며, 해당 부모에게만 알림 전송.

## 변경 파일 목록

### DB 스키마
- `photos` 테이블: `target_user_id INT NOT NULL DEFAULT 0` 컬럼 추가 (ALTER TABLE)

### Model
- `src/model/db/childcheck/photos.py`: `target_user_id` 필드 추가

### API (src/app/page.note.photo/api.py)
- `get_children_list()` 함수 추가: 교사는 본인 반 아이, 원장은 전체 아이 목록 반환
- `get_photos()` 수정: 아이 카테고리에서 target_user_id 기반 필터링 (부모는 자신의 ID로 자동 필터)
- `upload_photo()` 수정: target_user_id 파라미터 저장, 아이사진 업로드 시 해당 부모에게만 알림

### UI (src/app/page.note.photo/)
- `view.ts`: child_list 모드 추가, selectChild() 메서드, goBack() 네비게이션 분기, 부모→바로 사진 로드
- `view.pug`: 아이 목록 UI (child-card), 부모도 "아이사진" 메뉴 표시, 동적 제목(getListTitle)
- `view.scss`: .child-list, .child-card, .child-avatar, .child-info, .child-name, .child-class 스타일 추가
