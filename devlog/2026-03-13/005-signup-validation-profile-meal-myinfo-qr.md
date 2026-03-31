# 회원가입 검증·프로필·식단·회원정보·QR 일괄 구현 (7건)

- **ID**: 005
- **날짜**: 2026-03-13
- **유형**: 기능 추가

## 작업 요약
회원가입 이메일/전화번호 형식 검증, 원장 프로필 교사 상세 보기, 식단표 + 버튼 삭제, 회원정보 전화번호 자동 하이픈, 원장 서버 회원 코드 표시, 로그인 서버 생성 링크, 원장 QR 코드 표시 등 7건 일괄 구현.

## 변경 파일 목록

### FN-0014: 회원가입 이메일/전화번호 형식 검증
- `page.signup/view.ts`: `isValidEmail`, `isValidPhone` getter 추가, `isStep1Complete`에 전화번호 검증, `isStep2Complete`에 이메일 형식 검증 반영
- `page.signup/view.pug`: 이메일/전화번호 입력 필드에 에러 상태 클래스(`[class.error]`), 에러 아이콘(✗), 에러 메시지 표시
- `page.signup/view.scss`: `.error`, `.error-icon`, `.error-msg` 스타일 추가

### FN-0015: 원장 프로필에서 교사 상세 보기
- `page.note.profile/api.py`: 교사 쿼리에 `Users.phone` 추가, `phone` 필드 반환
- `page.note.profile/view.pug`: 교사 카드에 `.card-bottom` (프로필 보기 버튼) + `.card-detail` (전화번호 표시) 추가

### FN-0016: 식단표 날짜별 + 버튼 삭제
- `page.note.meal/view.pug`: `.header-plus` 요소 제거, 등록 폼(showForm) 관련 UI도 제거

### FN-0017: 회원정보 전화번호 자동 하이픈
- `page.myinfo/view.ts`: `formatPhone()` 메서드 추가
- `page.myinfo/view.pug`: 전화번호 편집 input에 `(ngModelChange)="formatPhone()"` 바인딩

### FN-0018: 원장 서버 회원 코드 표시
- `page.myinfo/api.py`: `Servers` 모델 import, `get_myinfo()`에서 원장인 경우 `server_code` 조회·반환
- `page.myinfo/view.ts`: `serverCode` 변수 추가, `loadMyInfo()`에서 매핑
- `page.myinfo/view.pug`: 역할 필드 아래에 원장 전용 서버 회원 코드 필드 (readonly) 추가

### FN-0019: 로그인 페이지 서버 생성 링크
- `page.main/view.pug`: 하단에 "서버 생성" 링크 추가
- `page.main/view.ts`: `goServerCreate()` 메서드 추가

### FN-0020: 원장 QR 코드 표시
- `page.note/api.py`: `get_qr_code()` 함수 추가 (qrcode 라이브러리로 base64 이미지 생성)
- `page.note/view.ts`: `showQR`, `qrImage`, `qrUrl` 변수 + `toggleQR()` 메서드 추가
- `page.note/view.pug`: 원장 전용 QR 코드 토글 버튼 + 이미지 표시 영역
- `page.note/view.scss`: `.qr-section`, `.qr-toggle-btn`, `.qr-content`, `.qr-image` 스타일 추가
- pip: `qrcode[pil]` 설치
