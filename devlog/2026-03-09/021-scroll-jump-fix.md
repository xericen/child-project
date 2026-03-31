# 노트 서브페이지 스크롤 점프 현상 수정

- **ID**: 021
- **날짜**: 2026-03-09
- **유형**: 버그 수정

## 작업 요약
meal/photo/myinfo의 `.container`가 `align-items: flex-start` + padding을 사용하여 today/profile의 `align-items: center`와 불일치, 페이지 전환 시 스크롤 점프 발생. 모든 서브페이지를 `align-items: center`로 통일하고 padding 제거.

## 변경 파일 목록
- **page.note.meal/view.scss**: `align-items: center`, padding 제거
- **page.note.photo/view.scss**: `align-items: center`, padding 제거
- **page.myinfo/view.scss**: `align-items: center`, padding 제거
