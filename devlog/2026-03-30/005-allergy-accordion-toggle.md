# 알레르기 섹션 아코디언 토글 추가

- **ID**: 005
- **날짜**: 2026-03-30
- **유형**: 기능 추가

## 작업 요약
교사/원장 통계 페이지의 "이번 주 알레르기 주의" 섹션에 접기/펼치기 아코디언 토글 추가. 기본 접힌 상태.

## 변경 파일 목록
### page.note.meal/view.ts
- `allergyExpanded: boolean = false` 토글 상태 변수 추가

### page.note.meal/view.pug
- `.ns-section-title-toggle` 클릭 가능 헤더 + `.ns-toggle-arrow` 화살표 추가
- 알레르기 목록 컨텐츠를 `*ngIf="allergyExpanded"` 래핑

### page.note.meal/view.scss
- `.ns-section-title-toggle` (flex, cursor pointer) 스타일 추가
- `.ns-toggle-arrow` (rotate 180deg when expanded) 스타일 추가
