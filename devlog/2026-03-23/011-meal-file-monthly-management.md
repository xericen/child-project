# 식단표 파일 월별 관리

- **ID**: 011
- **날짜**: 2026-03-23
- **유형**: 기능 추가

## 작업 요약
식단 안내 파일을 월별로 관리하도록 개선. 이번달/다음달 파일을 섹션 분리하여 표시하고, 업로드 시 대상 월을 선택할 수 있도록 함. 매월 1일 자정에 전월 파일 자동 삭제 스케줄러 추가.

## 변경 파일 목록

### 백엔드
- `src/app/page.note.meal/api.py`
  - `get_meal_files()`: 이번달/다음달 필터링, `current_files`/`next_files` 분리 반환
  - `upload_meal_file()`: `target_month` 파라미터 추가, meta.json에 대상 월 저장

### 스케줄러
- `src/route/api.scheduler/controller.py`
  - `cleanup_meal_files()` 함수 추가: 전월 이전 파일 & meta 엔트리 삭제
  - `cleanup-meal-files` 라우트 액션 추가
  - `import os` 추가
- `scripts/scheduler.py`
  - `run_meal_file_cleanup()` 함수 추가
  - 매일 00:05에 실행, 1일인 경우만 cleanup 실행

### 프론트엔드
- `src/app/page.note.meal/view.ts`
  - `currentMonthFiles`, `nextMonthFiles`, `currentMonthLabel`, `nextMonthLabel`, `uploadTargetMonth` 프로퍼티 추가
  - `loadMealFiles()`: 월별 데이터 분리 로드
  - `uploadMealFile()`: `target_month` 전송
- `src/app/page.note.meal/view.pug`
  - 업로드 폼에 대상 월 선택 드롭다운 추가
  - 파일 목록을 이번달/다음달 섹션으로 분리
- `src/app/page.note.meal/view.scss`
  - `.file-month-select`, `.file-month-group`, `.file-month-label` 스타일 추가
