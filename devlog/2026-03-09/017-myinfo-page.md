# 회원정보 페이지 생성 (조회 + 편집)

- **ID**: 017
- **날짜**: 2026-03-09
- **유형**: 기능 추가

## 작업 요약
page.myinfo 생성. 사용자 이메일, 역할, 자녀 정보(이름/생년월일/쌍둥이 여부), 알레르기 정보(종류/중증/대체식) 조회 화면과 편집 모드 구현. children/child_allergies 테이블 업데이트 기능 포함.

## 변경 파일 목록
### page.myinfo (신규 생성)
- **app.json**: page 모드, viewuri=/myinfo, controller=base, layout=layout.navbar
- **view.ts**: 조회/편집 모드 토글, 알레르기 토글, 저장/취소 로직
- **view.pug**: 이메일(읽기전용), 자녀정보, 알레르기 체크/토글 UI (view/edit 모드)
- **view.scss**: childcheck 스타일 기반, info-row 뷰 모드 추가
- **api.py**: get_myinfo() (users+children+child_allergies 조인 조회), save_myinfo() (children 업데이트+알레르기 교체)
