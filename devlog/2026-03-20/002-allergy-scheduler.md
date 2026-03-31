# 매일 오전 8시 알레르기 식단 알림 스케줄러

- **ID**: 002
- **날짜**: 2026-03-20
- **유형**: 기능 추가

## 작업 요약
매일 오전 8시에 당일 식단의 알레르기 성분과 원생의 알레르기를 매칭하여 부모/교직원에게 자동 푸시+인앱 알림을 보내는 스케줄러 시스템을 구현했다.

## 변경 파일 목록

### Route (신규)
- `src/route/api.scheduler/controller.py`
  - `/api/scheduler/allergy-check` 엔드포인트: API 키 인증 → 당일 식단별 알레르기 번호 수집 → 서버별 아이 알레르기 매칭 → 부모+교직원 알림 전송
  - `ALLERGY_MAP`, `ALLERGY_TYPE_TO_NUMBERS` 매핑 포함
  - 매칭 시 부모에게 개별 알림, 교직원에게 요약 알림
  - 매칭 없을 시 교직원에게만 "해당 원생 없음" 알림
- `src/route/api.scheduler/app.json`: route `/api/scheduler/<action>`, controller 없음

### 스케줄러 스크립트 (신규)
- `scripts/scheduler.py`: Python schedule 라이브러리 기반, 매일 08:00 Route 호출
- `scripts/allergy-cron.sh`: scheduler.py 실행 래퍼

### 설정
- `run.sh`: 서버 시작 시 스케줄러 백그라운드 자동 실행 추가

### 의존성
- `schedule` 1.2.2 패키지 설치
