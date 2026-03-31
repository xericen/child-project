# 초록색 텍스트 렌더링 + 테마 이름 정정 + 재파싱

- **ID**: 002
- **날짜**: 2026-03-26
- **유형**: 기능 수정

## 작업 요약
1. HWP 재파싱 실행: 17개 식단 레코드에 `{{green:...}}` 초록색 마커 반영
2. 오늘의 식단(page.note.today)에 `formatMealContent()` 추가하여 초록색 텍스트 렌더링
3. MEAL_THEMES를 실제 테마명(이달의식재료/세계밥상/상영양식/차차밥상/新메뉴/신선식품/대체식)으로 변경
4. HWP 이미지→테마 매핑 정보(THEME_IMAGE_MAP) 추가

## 변경 파일 목록

### `src/app/page.note.today/view.ts`
- `formatMealContent()` 메서드 추가: `{{green:텍스트}}` → `<span class="green-text">텍스트</span>` 변환

### `src/app/page.note.today/view.pug`
- `.card-content {{ menu }}` → `.card-content('[innerHTML]'="formatMealContent(menu)")` 변경 (3개소: 오전/점심/오후)

### `src/app/page.note.today/view.scss`
- `.card-content ::ng-deep .green-text` 스타일 추가 (color: #008000, font-weight: 600)

### `src/app/page.note.meal/api.py`
- `MEAL_THEMES` 7가지 이름/이모지/키워드를 실제 HWP 기준으로 변경
- `THEME_IMAGE_MAP` 추가 (HWP 이미지 파일명 → 테마명 매핑)

### `src/app/page.note.meal/view.ts`
- `MEAL_THEMES` readonly 객체를 실제 테마명/이모지/색상으로 변경

## 테마 추출 한계
HWP 분석 결과, 테마 아이콘은 헤더 설명란에만 존재하고 개별 날짜의 점심 셀에는 배치되지 않아 자동 테마 할당이 불가능. theme=NULL 상태 유지. 향후 화성시 급식관리지원센터의 HWP 양식 변경 시 이미지 기반 테마 감지 가능.
