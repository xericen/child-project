# 원장 가입 승인 시스템 구현

- **ID**: 007
- **날짜**: 2026-03-10
- **유형**: 기능 추가

## 작업 요약
원장 전용 가입 승인 페이지(page.note.approve) 생성. 미승인 사용자 목록 표시, 승인/거절 기능 구현. 로그인 시 approved=False인 사용자 차단 로직은 FN-0005에서 이미 구현됨.

## 변경 파일 목록
- `src/app/page.note.approve/` (신규): api.py, view.ts, view.pug, view.scss, app.json
  - api.py: get_pending_users(), approve_user(), reject_user()
  - view.ts: 승인 대기 목록 로드, 승인/거절 처리
  - view.pug: 카드형 리스트 UI
  - view.scss: 승인 카드 스타일
