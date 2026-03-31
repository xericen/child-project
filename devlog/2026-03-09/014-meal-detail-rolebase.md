# 식단표 상세 페이지 역할별 기능 구현

- **ID**: 014
- **날짜**: 2026-03-09
- **유형**: 기능 추가

## 작업 요약
식단표(page.note.meal) 페이지에 월간 캘린더 뷰, 날짜별 식단 상세 뷰, 식단 등록/삭제 기능 구현. meals DB 테이블 신규 생성. 교사/원장만 등록/삭제 가능, 부모는 조회만 가능.

## 변경 파일 목록
- `src/model/db/childcheck/meals.py` — 신규: meals Peewee 모델
- `src/app/page.note.meal/view.ts` — 월간/날짜별 모드 전환, 식단 등록 폼, CRUD
- `src/app/page.note.meal/view.pug` — 캘린더 UI, 식단 카드, 등록 폼
- `src/app/page.note.meal/view.scss` — 캘린더, 폼, 카드 스타일
- `src/app/page.note.meal/api.py` — get_monthly, get_daily, save_meal, delete_meal
- `src/app/page.note.today/api.py` — meals DB 실제 연동
