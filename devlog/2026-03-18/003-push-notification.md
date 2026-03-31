# 푸시 알림(Web Push Notification) 구현

- **ID**: 003
- **날짜**: 2026-03-18
- **유형**: 기능 추가

## 작업 요약
Web Push API를 활용하여 앱 설치된 기기(Android/iOS/PC)에 실제 푸시 알림 전송 기능 구현. VAPID 인증, 구독 관리, 알림 발송 전체 파이프라인 완성.

## 변경 파일 목록

### 패키지 설치
- `pywebpush 2.3.0` (py-vapid, http-ece 포함)

### Config
- `config/push.py`: VAPID 공개키/개인키 설정 (신규)
- `config/pwa/sw.js`: push, notificationclick 이벤트 핸들러 추가

### DB
- `push_subscriptions` 테이블 생성 (user_id, endpoint, p256dh, auth, device_type, created_at)

### Model
- `src/model/db/childcheck/push_subscriptions.py`: Peewee ORM 모델 (신규)
- `src/model/push.py`: PushService 유틸리티 - subscribe, unsubscribe, send_to_user (신규)

### App API
- `page.main/api.py`: `get_vapid_key()`, `subscribe_push()` 함수 추가
- `page.note.photo/api.py`: `notify_server_parents()` + 개별 알림에 push 발송 연동
- `page.note.meal/api.py`: `notify_parents()`에 push 발송 연동
- `page.signup/api.py`: `notify_directors()`에 push 발송 연동

### App Frontend
- `page.main/view.ts`: `subscribePush()`, `urlBase64ToUint8Array()` 추가. 로그인 성공 후 자동 구독.
