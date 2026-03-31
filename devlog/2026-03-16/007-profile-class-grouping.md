# 원장 프로필 - 반별 그룹핑 UI 변경

- **ID**: 007
- **날짜**: 2026-03-16
- **유형**: 기능 추가

## 작업 요약
원장 프로필 페이지(`page.note.profile`)에서 교사와 어린이를 반(class_name) 기준으로 그룹핑하여 표시.
기존 "교사" / "어린이" 분리 구조 → 반별 섹션 아래 교사 카드 → 어린이 카드 순서로 배치.
교사 뷰는 기존대로 본인 반 어린이만 표시.

## 변경 파일 목록
### 백엔드
- `src/app/page.note.profile/api.py`: `get_profile_data()`에 `classes` 배열 추가 (반별 교사+어린이 그룹핑, 미지정 그룹 마지막 정렬)

### UI
- `src/app/page.note.profile/view.ts`: `classes` 배열 수신·상태 관리, 삭제 후 `loadData()` 재호출로 그룹핑 갱신
- `src/app/page.note.profile/view.pug`: 원장 뷰를 `classes` 기반 반별 섹션으로 변경, 교사 뷰는 기존 유지
- `src/app/page.note.profile/view.scss`: `.section-title` 스타일 추가
