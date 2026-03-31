# users 테이블 app_installed 컬럼 추가 + 로그인 흐름 변경

- **ID**: 025
- **날짜**: 2026-03-17
- **유형**: 기능 추가

## 작업 요약
앱 설치 여부를 DB에 영구 기록하여 isStandalone() 대신 DB 기반으로 install 페이지 분기. users 테이블에 app_installed 컬럼 추가, 로그인/childcheck 완료 시 DB 값 기준으로 install 페이지 표시 여부 결정, 설치/건너뛰기 시 app_installed=1 저장.

## 변경 파일 목록
### DB 스키마
- **src/model/db/login_db/users.py**: `app_installed = pw.BooleanField(default=False)` 컬럼 추가
- **MySQL**: `ALTER TABLE users ADD COLUMN app_installed TINYINT(1) NOT NULL DEFAULT 0` 실행

### page.main
- **api.py**: login 응답에 `app_installed=bool(user.app_installed)` 추가
- **view.ts**: `navigateAfterLogin()`에서 `isStandalone()` 제거, `appInstalled` 파라미터 기반 분기

### page.childcheck
- **api.py**: `get_child_info()` 응답에 `app_installed` 추가
- **view.ts**: `isStandalone()` 제거, `appInstalled` 변수로 install 페이지 분기

### page.pwa.install
- **api.py**: 신규 생성 — `mark_installed()` 함수 (app_installed=1 업데이트)
- **view.ts**: `confirmInstall()` 성공 시 + `goToNote()` 건너뛰기 시 `mark_installed` API 호출
