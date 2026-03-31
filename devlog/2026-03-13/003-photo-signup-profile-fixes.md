# 식단 사진·회원가입·프로필 버그 수정 및 기능 추가 (6건)

- **ID**: 003
- **날짜**: 2026-03-13
- **유형**: 버그 수정 | 기능 추가

## 작업 요약
FN-0004~FN-0009 총 6건의 작업을 일괄 수행. 식단표 사진 표시 수정, 알레르기 없는 부모 버튼 숨김, 회원가입 보안 개선(인증 전 DB 생성 방지), 프로필 페이지 UI 수정, 생일 이모티콘 표시 기능 추가.

## 변경 파일 목록

### page.note.photo/api.py (FN-0004, FN-0005)
- `serve_photo()`: 파일 확장자 fallback 로직 추가 (.jpg↔.jpeg)
- `get_role()`: 학부모 대상 `has_allergy` 필드 반환 추가

### page.note.photo/view.ts (FN-0005)
- `hasAllergy: boolean = false` 프로퍼티 추가
- `ngOnInit()`에서 API 응답의 `has_allergy` 바인딩

### page.note.photo/view.pug (FN-0005)
- 아이맞춤 식단 버튼에 `*ngIf="role !== 'parent' || hasAllergy"` 조건 추가

### page.signup/view.pug (FN-0006)
- Step 1에 "← 로그인으로 돌아가기" 링크 추가 (`navigate('/')`)

### page.signup/api.py (FN-0007)
- `send_code()`: `Users.create()` 제거, 가입 정보를 세션(`signup_data`)에 JSON으로 임시 저장
- `verify_code()`: 인증코드 확인 후 세션에서 가입 데이터를 꺼내 `Users.create(verified=True)` 수행
- 이메일 중복 재확인 로직 추가 (인증 지연 사이 race condition 방지)

### page.note.profile/view.pug (FN-0008, FN-0009)
- `!child.has_childcheck` 조건의 `.card-detail` 블록(부모 이름/전화번호) 제거 — "아이 체크 미완료" 텍스트만 표시
- `.card-name`에 `*ngIf="child.is_birthday"` 조건으로 🎂 이모티콘 표시 추가

### page.note.profile/api.py (FN-0009)
- `get_profile_data()`의 children 데이터에 `is_birthday` 필드 추가 (today.month/day 비교)
