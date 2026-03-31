# 알림 시스템 구현 (DB + 백엔드 + 프론트)

- **ID**: 018
- **날짜**: 2026-03-09
- **유형**: 기능 추가

## 작업 요약
notifications DB 테이블 생성 및 Peewee 모델 작성. layout.navbar에서 알림 벨 클릭 시 알림 목록 패널 출현, 읽지 않은 알림 배지, 읽음 처리, 전체 읽음 기능 구현. 식단표/사진 업로드 시 부모 역할 사용자들에게 자동 알림 생성 연동.

## 변경 파일 목록
### DB
- **notifications 테이블**: 신규 생성 (user_id, type, title, message, link, is_read, created_at)
- **src/model/db/childcheck/notifications.py**: Peewee 모델 (신규)

### layout.navbar
- **api.py**: get_unread_count, get_notifications, read_notification, read_all, logout
- **view.ts**: 알림 토글, 알림 목록 로드, 개별/전체 읽음 처리, timeAgo 표시
- **view.pug**: 알림 패널 UI (헤더+목록/빈상태, 모두읽음 버튼)
- **view.scss**: 알림 패널, noti-item(읽음/안읽음 구분) 스타일

### page.note.meal
- **api.py**: notify_parents() 함수 추가, save_meal()에서 식단 등록 후 부모 알림 생성

### page.note.photo
- **api.py**: notify_parents() 함수 추가, upload_photo()에서 사진 업로드 후 부모 알림 생성
