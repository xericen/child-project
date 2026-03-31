# 스케줄러 알람 정상작동 검증

- **ID**: 006
- **날짜**: 2026-03-27
- **유형**: 검증 / 개선

## 작업 요약
스케줄러(매일 08:00 KST 알레르기 알림)가 정상 작동하는지 검증. curl 차단은 VS Code 정책이며, 스케줄러는 Python urllib을 사용하므로 무관. 수동 테스트 성공(HTTP 200). 디버그 로그 추가.

## 변경 파일 목록

### scripts/scheduler.py
- while 루프에 `schedule.idle_seconds()` 기반 다음 실행 시간 로그 추가
