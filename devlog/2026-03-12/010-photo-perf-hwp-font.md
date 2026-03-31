# 사진 페이지 성능 개선 및 HWP→PDF 한글 폰트 설치

- **ID**: 010
- **날짜**: 2026-03-12
- **유형**: 기능 개선 | 버그 수정

## 작업 요약
식단 사진 페이지의 4가지 이슈를 일괄 수정: (1) 오늘 날짜 자동 생성 제거, (2) 사진 업로드 시 알림을 별도 스레드로 분리하여 응답 속도 개선, (3) 사진 서빙에 캐시 헤더 추가 및 이미지 lazy loading 적용, (4) HWP→PDF 변환 시 한글 깨짐 해결을 위한 폰트 설치.

## 변경 파일 목록

### api.py (`page.note.photo/api.py`)
- `_build_days_response()`: 오늘 날짜 자동 삽입 코드(today auto-insert) 4줄 삭제
- `upload_photo()`: `notify_server_parents()` 및 개별 알림 생성을 `threading.Thread(daemon=True)`로 분리하여 비동기 실행
- `serve_photo()`: `flask.send_file()` + `Cache-Control: public, max-age=86400` 헤더 추가
- 상단에 `import threading` 추가

### view.pug (`page.note.photo/view.pug`)
- 공용 캘린더 및 아이 캘린더의 `img.slot-photo` 태그에 `loading="lazy"` 속성 추가 (2곳)

### 시스템 패키지
- `fonts-nanum`, `fonts-noto-cjk` 설치 → `fc-cache -fv` 실행
