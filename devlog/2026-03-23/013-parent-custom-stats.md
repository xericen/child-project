# 부모용 맞춤 통계 (내 아이 중심 뷰)

- **ID**: 013
- **날짜**: 2026-03-23
- **유형**: 기능 추가

## 작업 요약
부모 로그인 시 통계 페이지 최상단에 "우리 아이 식단 안전" 섹션 추가. 자녀 이름, 연령대별 열량 기준 자동 적용, 알레르기 정보, 이번 주 주의 식단(실제 음식명 포함)을 개인화하여 표시.

## 변경 파일 목록

### 백엔드
- `src/app/page.note.meal/api.py`
  - `KEYWORD_ALIASES` 상수 추가
  - `_keyword_in_content()` 헬퍼 함수 추가
  - `get_parent_stats()` 함수 추가: 자녀 목록 + 연령 계산(birthdate→age_group) + 알레르기 조회 + 이번 주 식단 알레르기 매칭(식단명 포함)

### 프론트엔드
- `src/app/page.note.meal/view.ts`
  - `parentData`, `parentChildren` 프로퍼티 추가
  - `goStats()`: 부모일 때 `loadParentStats()` 추가 호출
  - `loadParentStats()`: 자녀 연령대로 자동 age 선택 + 캘린더 갱신
- `src/app/page.note.meal/view.pug`
  - 통계 모드 내 부모 전용 `.ns-parent-section` 추가
  - 자녀 카드(이름, 연령, 알레르기 태그, 주의 식단 리스트)
- `src/app/page.note.meal/view.scss`
  - `.ns-parent-section`, `.ns-child-card`, `.ns-child-header`, `.ns-allergy-tag`, `.ns-alert-*`, `.ns-child-safe` 등 스타일
