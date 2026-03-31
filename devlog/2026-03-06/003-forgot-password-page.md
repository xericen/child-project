# 비밀번호 찾기 페이지 생성 (page.forgot)

- **ID**: 003
- **날짜**: 2026-03-06
- **유형**: 기능 추가

## 작업 요약
비밀번호 찾기 페이지 신규 생성. 3단계 스텝(닉네임+이메일 → 인증코드 6자리 → 새 비밀번호 설정)으로 구성. signup 페이지와 동일한 디자인 적용.

## 변경 파일 목록

### src/app/page.forgot/ (신규 생성)
- **app.json**: viewuri `/forgot`, layout `layout.navbar`, controller `base`
- **view.pug**: 3단계 UI (step-indicator, 인증코드 6자리 입력, 비밀번호 확인 입력)
- **view.ts**: step 관리, 인증코드 입력 핸들러(trackBy+[value] 적용), 비밀번호 일치 검증
- **api.py**: `send_code()` 닉네임+이메일 DB 조회 후 인증코드 발송, `verify_code()` 세션 코드 검증, `reset_password()` 비밀번호 업데이트
- **view.scss**: signup 스타일 재사용 + `.error-text` 추가
