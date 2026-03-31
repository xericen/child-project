# UI 개선 및 식단 사진 로딩 최적화

- **ID**: 001
- **날짜**: 2026-03-13
- **유형**: 기능 추가 / 버그 수정

## 작업 요약
5가지 작업을 일괄 수행: 일별 식단 삭제버튼 제거, 프로필 교사/학생 삭제 기능, 회원가입 이름+전화번호 변경, 아이 프로필 부모정보 표시, 식단 사진 로딩 최적화(이미지 압축).

## 변경 파일 목록

### DB 스키마
- `src/model/db/login_db/users.py`: phone 컬럼(VARCHAR 20, NULL) 추가
- ALTER TABLE 실행 완료

### 일별 식단 페이지
- `src/app/page.note.meal/view.pug`: 삭제 버튼(✕) 제거, 편집 버튼만 유지
- `src/app/page.note.meal/api.py`: PIL import 및 _compress_image 헬퍼 추가, save_meal()에서 사진 업로드 시 압축 적용

### 프로필 페이지 (원장 권한)
- `src/app/page.note.profile/api.py`: delete_teacher(), delete_child() 함수 추가 (DB cascade 삭제), 부모 이름/전화번호 쿼리 추가
- `src/app/page.note.profile/view.ts`: deleteTeacher(), deleteChild() 메서드 추가
- `src/app/page.note.profile/view.pug`: 교사/학생 삭제 버튼 추가, 부모 이름/전화번호 표시
- `src/app/page.note.profile/view.scss`: .btn-delete 스타일 추가

### 회원가입 페이지
- `src/app/page.signup/view.pug`: 닉네임→이름 라벨 변경, 전화번호 입력 필드 추가
- `src/app/page.signup/view.ts`: phone 프로퍼티 및 sendCode 파라미터 추가
- `src/app/page.signup/api.py`: phone 파라미터 수신 및 Users.create()에 전달

### 식단 사진 최적화
- `src/app/page.note.photo/api.py`: PIL import, _compress_image() 헬퍼, upload_photo()에서 압축 적용, serve_photo() 캐시 헤더 강화 (7일 + ETag)
- 기존 사진 일괄 압축 실행: 11개 파일 2929KB → 246KB (92% 감소)
