# 식단표 페이지 파일 업로드 기능 추가

- **ID**: 003
- **날짜**: 2026-03-12
- **유형**: 기능 추가

## 작업 요약
식단표 페이지 메뉴 모드에서 "조회 방식을 선택해주세요" 텍스트를 제거하고, 그 자리에 식단 안내 파일 업로드/다운로드 영역을 추가. 원장/교사는 파일 업로드 및 삭제, 부모는 파일 열람/다운로드 가능. 월간/날짜별 조회 버튼은 파일 영역 아래로 이동.

## 변경 파일 목록
- `src/app/page.note.meal/view.pug`: 메뉴 모드에 file-section 추가, subtitle 제거
- `src/app/page.note.meal/view.ts`: mealFiles, selectedMealFile 상태 추가, loadMealFiles/uploadMealFile/downloadMealFile/deleteMealFile 메서드 추가
- `src/app/page.note.meal/api.py`: get_meal_files, upload_meal_file, delete_meal_file, serve_meal_file 4개 API 함수 추가 (meta.json 기반 파일 관리)
- `src/app/page.note.meal/view.scss`: file-section 관련 스타일 추가
