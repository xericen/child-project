# 공용사진 전체 공개 + 서버 격리

- **ID**: 013
- **날짜**: 2026-03-11
- **유형**: 기능 추가

## 작업 요약
photos 테이블에 server_id 컬럼 추가하여 서버별 사진 격리 구현. 공용사진을 교사/부모/원장 모두 열람 가능하도록 수정. 부모는 아이사진 카테고리 숨김. 알림도 같은 서버 부모에게만 발송하도록 변경.

## 변경 파일 목록
- DB: `childcheck.photos` 테이블에 `server_id INT NOT NULL DEFAULT 0` 컬럼 + 인덱스 추가
- `src/model/db/childcheck/photos.py`: server_id 필드 추가
- `src/app/page.note.photo/api.py`: get_photos에 server_id 필터 추가, upload_photo에 server_id 저장, notify_server_parents로 서버별 알림
- `src/app/page.note.photo/view.ts`: canUpload() 헬퍼 추가
- `src/app/page.note.photo/view.pug`: 부모는 아이사진 메뉴 숨김, canUpload() 조건 적용
