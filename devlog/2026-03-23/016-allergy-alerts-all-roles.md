# 원장/교사 이번 주 알레르기 주의 기능 확장

- **ID**: 016
- **날짜**: 2026-03-23
- **유형**: 기능 추가

## 작업 요약
원장과 교사도 식단 통계에서 "이번 주 알레르기 주의" 섹션을 볼 수 있도록 확장. 원장은 전체 아이, 교사는 담당 반의 아이 알레르기만 표시. 원장 뷰에서 아이 이름 옆에 반 정보(class_name) 표시.

## 변경 파일 목록

### API (백엔드)
- `page.note.meal/api.py`: `get_parent_stats()` 함수를 역할별로 분기. parent=자녀 조회, director=서버 전체 아이 조회, teacher=담당 반 아이만 조회. 반환 데이터에 `class_name` 필드 추가.

### 프론트엔드 (UI)
- `page.note.meal/view.ts`: `loadParentStats()`를 모든 역할에서 호출. director/teacher는 알레르기 있는 아이만 필터링.
- `page.note.meal/view.pug`: 알레르기 섹션 `*ngIf` 조건에서 `role === 'parent'` 제거. 역할별 다른 제목 표시 (부모=우리 아이 식단 안전, 원장=이번 주 알레르기 주의, 교사=우리반 알레르기 주의). 아이 이름 옆에 반 정보 표시 (director/teacher).
- `page.note.meal/view.scss`: `.ns-child-class` 스타일 추가.
