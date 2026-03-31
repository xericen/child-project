# childcheck 알레르기 수정 가능화 + 반 삭제 에러 처리 개선

- **ID**: 011
- **날짜**: 2026-03-25
- **유형**: 버그 수정

## 작업 요약
이세영(학부모) → 아이 이지용이 children 테이블에 이미 등록되어 있어 childcheck_done=True이므로
childcheck 페이지를 다시 볼 수 없었고, 알레르기 입력 기회가 없었다.
학부모 홈 메뉴에 "아이 정보 수정" 링크를 추가하고, childcheck API를 upsert 방식으로 변경.
반 삭제 except:pass 에러 숨김도 제거하여 실제 오류 메시지가 UI에 표시되도록 수정.

## 변경 파일 목록

### `src/app/page.childcheck/api.py`
- `get_child_info()`: users 테이블 대신 **children 테이블**에서 기존 아이 정보 로드. child_allergies 테이블에서 기존 알레르기 목록·is_severe·needs_substitute도 함께 반환. 아이가 없으면 users 테이블 보조 데이터 반환.
- `save_childcheck()`: `Children.create()` → **upsert** 방식 (기존 children 레코드 있으면 update, 없으면 create). child_allergies는 기존 레코드 모두 삭제 후 재삽입.

### `src/app/page.childcheck/view.ts`
- `loadChildInfo()`: 서버에서 받은 알레르기 목록(allergies 배열)을 파싱하여 **체크박스 초기값** 복원. twinType, isSevere, needsSubstitute도 초기화.

### `src/app/page.note/view.ts`
- `buildMenu()`: parent 역할 메뉴에 `{ icon: '🌿', label: '아이 정보 수정', path: '/childcheck' }` 추가.

### `src/app/page.note.profile/api.py`
- `delete_class()`: 교사 삭제 블록·학부모 삭제 블록의 `except Exception: pass` → `except Exception as e: errors.append(...)`. 에러 발생 시 500으로 반환하여 UI에 실제 오류 메시지 표시.
