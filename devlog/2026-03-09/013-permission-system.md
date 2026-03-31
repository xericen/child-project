# 권한 시스템 적용

- **ID**: 013
- **날짜**: 2026-03-09
- **유형**: 기능 추가

## 작업 요약
전체 페이지에 역할 기반 권한 체크 적용 완료 확인. 원장(director): 전체 권한, 교사(teacher): 식단검수/사진업로드, 부모(parent): 조회만. 각 api.py에서 세션 role 체크, 프론트에서 역할별 UI 표시/숨김 처리.

## 권한 매트릭스
| 기능 | 부모 | 교사 | 원장 |
|------|------|------|------|
| 식단 조회 | ✅ | ✅ | ✅ |
| 식단 등록 (+버튼) | ❌ | ✅ | ✅ |
| 사진 조회 | ✅ | ✅ | ✅ |
| 사진 업로드 (+버튼) | ❌ | ✅ | ✅ |
| 아이 프로필 접근 | ❌ | ✅ | ✅ |
| childcheck | ✅ | ❌ | ❌ |

## 적용 위치
- `page.note/api.py`: get_role() - 역할별 메뉴 버튼 구성
- `page.note.today/api.py`: get_today_menu() - 역할 반환
- `page.note.meal/api.py`: get_role() - + 버튼 표시 제어
- `page.note.photo/api.py`: get_role() - + 버튼 표시 제어
- `page.note.profile/api.py`: get_children_list() - 부모 403 반환
