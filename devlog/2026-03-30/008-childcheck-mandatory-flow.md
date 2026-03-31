# 부모 로그인 후 childcheck 필수 경유 플로우 수정

- **ID**: 008
- **날짜**: 2026-03-30
- **유형**: 버그 수정

## 작업 요약
부모 로그인 시 `_get_allergy_check_completed()`가 Children 레코드 존재만으로 `True` 반환하여 childcheck를 건너뛰는 문제 수정. `allergy_checked` 컬럼 추가하여 `save_childcheck()` 완료 시에만 플래그가 설정되도록 변경.

## 변경 파일 목록
### DB 스키마
- `children` 테이블에 `allergy_checked TINYINT(1) DEFAULT 0` 컬럼 추가
- 기존 알레르기 데이터가 있는 3건의 레코드를 `allergy_checked=1`로 마이그레이션

### src/model/db/childcheck/children.py
- `allergy_checked = pw.BooleanField(default=False)` 필드 추가

### page.childcheck/api.py
- `save_childcheck()`: Children 업데이트/생성 시 `allergy_checked=True` 설정

### page.main/api.py
- `_get_allergy_check_completed()`: `child is not None` → `child is not None and child.allergy_checked` 조건으로 변경
