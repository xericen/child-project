# 문의하기·회원가입·사진업로드·생일이모지 수정

- **ID**: 004
- **날짜**: 2026-03-13
- **유형**: 버그 수정 | 기능 개선

## 작업 요약
문의하기 API server_id fallback 버그 수정, 회원가입 로그인 돌아가기 스타일 통일, 사진 업로드 클라이언트 사전 압축으로 속도 개선, children 미등록 아이의 생일 이모티콘 미표시 버그 수정.

## 변경 파일 목록

### FN-0010: 문의하기 API 버그 수정
- `page.contact/api.py`: `server_id`에 `join_server_id` fallback 추가, `int()` 캐스팅 통일, `class_name` strip 처리

### FN-0011: 회원가입 로그인 돌아가기 스타일
- `page.signup/view.pug`: step 1 btn-row에서 `a.btn-back` 제거, `.bottom-row > a.link-gray` 패턴으로 하단에 추가 (비밀번호 변경 페이지와 동일)

### FN-0012: 사진 업로드 속도 개선
- `page.note.photo/view.ts`: Canvas API 기반 `compressImage()` 함수 추가 (1200px 리사이즈 + JPEG 압축), `onSlotFileSelected()`에 클라이언트 사전 압축 적용, `service.loading.show()/hide()` 로딩 표시 추가

### FN-0013: 생일 이모티콘 미표시 수정
- `page.note.profile/api.py`: Users select에 `birth_date` 추가, children 미등록(fallback) 경로에서 `users.birth_date`로 `is_birthday` 계산
