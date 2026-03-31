# 알레르기 알람 발송 시간 수정 (UTC 08:00 → KST 08:00)

- **ID**: 003
- **날짜**: 2026-03-25
- **유형**: 버그 수정

## 작업 요약
서버 timezone이 UTC여서 scheduler.py의 "08:00"이 KST 17:00에 실행되던 문제 수정. scheduler.py에 `TZ=Asia/Seoul` 설정, controller.py의 날짜 계산을 KST 기준으로 변경.

## 변경 파일 목록

### scripts/scheduler.py
- `os.environ['TZ'] = 'Asia/Seoul'` + `time.tzset()` 추가하여 KST 기준 스케줄 실행
- 주석 및 로그 메시지에 KST 명시

### route/api.scheduler/controller.py
- `KST = datetime.timezone(datetime.timedelta(hours=9))` 상수 추가
- `check_allergies()`: `datetime.date.today()` → `datetime.datetime.now(KST).date()`
- `cleanup_meal_files()`: 동일하게 KST 날짜 사용
