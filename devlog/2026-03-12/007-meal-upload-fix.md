# 식단표 파일 업로드 및 saveMeal fetch 전환

- **ID**: 007
- **날짜**: 2026-03-12
- **유형**: 버그 수정

## 작업 요약
식단표(page.note.meal) 페이지의 파일 업로드 버튼 미작동 문제 수정. `saveMeal()`을 `wiz.call()` → `fetch()`로 전환하여 FormData 파일 업로드를 지원하도록 개선. `onMealFileSelect`에 `await` 추가, ViewChild를 통한 파일 입력 리셋 처리.

## 변경 파일 목록

### page.note.meal/view.ts
- `saveMeal()`: `wiz.call("save_meal", formData)` → `fetch('/wiz/api/page.note.meal/save_meal', ...)` 전환 (FormData 파일 업로드 지원)
- `onMealFileSelect()`: `async` 추가 및 `await this.service.render()` 호출
- `@ViewChild('fileInput')` 추가로 업로드 후 파일 입력 초기화
- `uploadMealFile()`: 업로드 완료 후 `fileInput.nativeElement.value = ''` 초기화
