# 프로필 탭 전환 / 회원정보 탭 분리 / 타이틀 한줄 통일 / 프로필 사진 기능

- **ID**: 002
- **날짜**: 2026-04-09
- **유형**: 기능 추가

## 작업 요약
5개 UI 개선 작업을 일괄 수행: (1) 프로필 페이지 반별 탭 전환, (2) 회원정보 탭 분리(회원정보/알레르기), (3) 페이지 타이틀 한 줄 통일, (4) 노트 페이지 프로필 사진 업로드/표시, (5) 회원정보 19종 알레르기 체크 (FN-0002와 통합).

## 변경 파일 목록

### FN-0001: 프로필 페이지 반별 탭 전환
- `src/app/page.note.profile/view.ts` - selectedTab, tabNames, buildTabs(), selectTab(), applyFilter() 탭 기반 리팩토링
- `src/app/page.note.profile/view.pug` - .tab-bar 추가, 원장 뷰 단일 반 표시
- `src/app/page.note.profile/view.scss` - .tab-bar, .tab-item 스타일

### FN-0002+0005: 회원정보 탭 분리 + 19종 알레르기
- `src/app/page.myinfo/view.ts` - activeTab, standardAllergies(19종), switchTab(), toggleStandardAllergy(), hasAnyAllergy
- `src/app/page.myinfo/view.pug` - 탭 바(회원정보/알레르기), 19종 그리드 카드 UI
- `src/app/page.myinfo/view.scss` - tab-bar, allergy-grid, allergy-card 스타일

### FN-0003: 타이틀 한 줄 통일
- `src/app/page.note/view.pug` - `{{ titleName }}\nbr\nNote` → `{{ titleName }} Note`
- `src/app/page.note.today/view.pug` - `오늘의\nbr\n식단` → `오늘의 식단`
- `src/app/page.note.activity/view.pug` - `활동\nbr\n추천` → `활동추천`
- `src/app/page.note.approve/view.pug` - `가입\nbr\n승인` → `가입승인`
- `src/app/page.childcheck/view.pug` - `child\nbr\nCheck` → `child Check`, `알레르기\nbr\nCheck` → `알레르기 Check`

### FN-0004: 프로필 사진 기능
- `src/model/db/childcheck/children.py` - profile_photo 컬럼 추가 (VARCHAR 255)
- `src/app/page.note/api.py` - upload_profile_photo, serve_profile_photo, delete_profile_photo API 추가, get_role에 profile_photo 반환 추가
- `src/app/page.note/view.ts` - profilePhoto, uploading 속성, triggerPhotoUpload(), onPhotoSelected(), deleteProfilePhoto(), getProfilePhotoUrl()
- `src/app/page.note/view.pug` - 프로필 사진 원형 영역 (업로드/변경/삭제 버튼 포함)
- `src/app/page.note/view.scss` - .profile-photo-wrap, .profile-photo-img, .profile-photo-actions 스타일
- `src/app/page.note.profile/api.py` - children 데이터에 profile_photo 필드 추가, serve_profile_photo API 추가
- `src/app/page.note.profile/view.ts` - getProfilePhotoUrl() 메서드 추가
- `src/app/page.note.profile/view.pug` - 👶 이모지 → 실제 프로필 사진 조건부 표시
- `src/app/page.note.profile/view.scss` - .card-avatar 크기 고정 + .avatar-photo 스타일
