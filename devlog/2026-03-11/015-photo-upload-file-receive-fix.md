# 사진 업로드 파일 수신 버그 수정

- **ID**: 015
- **날짜**: 2026-03-11
- **유형**: 버그 수정

## 작업 요약
사진 업로드 시 400 에러(사진을 선택해주세요) 발생 — 원인 2가지:
1. `wiz.request.files()`는 내부적으로 `file[]` 필드명을 조회하는데, 프론트에서 `photo` 필드명으로 전송 → `wiz.request.file("photo")`로 변경
2. `fs.write(name, data, mode="wb")`는 지원하지 않음 → `fs.write.file(name, fileStorage)`로 변경

## 변경 파일 목록

### API
- `src/app/page.note.photo/api.py`: `upload_photo()` 함수에서 `wiz.request.files()` → `wiz.request.file("photo")`, `fs.write(name, file.read(), mode="wb")` → `fs.write.file(name, file)`
