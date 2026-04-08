# 어린이집명/반 표시 디자인 개선

- **ID**: 005
- **날짜**: 2026-04-08
- **유형**: 기능 추가

## 작업 요약
`page.note` 랜딩 페이지의 어린이집명(서버명)+반 표시를 기존 별도 pill 배지 2개(파란/주황)에서 통합된 카드형 디자인으로 개선. 학교 아이콘과 어린이집명, 반 태그를 하나의 카드 컴포넌트로 정리하여 가독성과 시각적 정돈감 향상.

## 변경 파일 목록

### UI (view.pug)
- `src/app/page.note/view.pug`: `.server-badge` + `.class-badge`를 `.school-card` 카드 컴포넌트로 교체 (icon + name + class tag)

### 스타일 (view.scss)
- `src/app/page.note/view.scss`: `.school-card` 관련 스타일 추가 (카드 배경, 아이콘 영역, 이름, 반 태그)
