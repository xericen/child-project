# created_at 타임존 KST 미반영 최종 수정

- **ID**: 004
- **날짜**: 2026-03-17
- **유형**: 버그 수정

## 작업 요약
`created_at` 타임존이 UTC로 저장되던 문제의 근본 원인 해결. 2가지 수정:
1. **MySQL 글로벌 타임존 변경**: `SET GLOBAL time_zone = '+09:00'` — 모든 커넥션(기존 캐시 포함)에서 KST 적용
2. **notifications 모델 수정**: `default=datetime.datetime.now` (Python UTC) → `DEFAULT CURRENT_TIMESTAMP` (MySQL KST) — WIZ 프레임워크의 캐시된 커넥션도 KST 시간을 사용

검증: WIZ API 경유로 meal + notification 생성 → 양쪽 모두 `created_at`이 KST(16:40) 확인.

## 변경 파일 목록
### Model
- `src/model/db/childcheck/notifications.py`:
  - `created_at = pw.DateTimeField(default=datetime.datetime.now)` → `pw.DateTimeField(constraints=[pw.SQL('DEFAULT CURRENT_TIMESTAMP')])`
  - `import datetime` 제거

### DB 설정
- MySQL 글로벌 타임존: `SYSTEM` → `+09:00` (SET GLOBAL time_zone)
