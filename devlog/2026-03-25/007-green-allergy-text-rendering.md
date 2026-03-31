# 급식 메뉴 초록색 알레르기 표기 텍스트 렌더링

- **ID**: 007
- **날짜**: 2026-03-25
- **유형**: 기능 추가

## 작업 요약
HWP 원본 식단표에서 초록색으로 표시된 알레르기 관련 텍스트(예: `[표고버섯나물⑤⑥]`)를 앱에서도 동일하게 초록색으로 렌더링하도록 구현. HWP→XHTML 변환 시 생성되는 `styles.css`에서 charshape 클래스의 색상 정보를 동적으로 파싱하여 초록색 클래스를 식별하고, 백엔드에서 `{{green:text}}` 마커로 표시한 뒤 프론트엔드에서 `<span class="green-text">` HTML로 변환하는 파이프라인 구축.

## 변경 파일 목록

### 백엔드 (api.py)
- **`src/app/page.note.meal/api.py`**
  - `_parse_meal_html(html_content, styles_css='')`: `styles_css` 파라미터 추가. 외부 styles.css와 인라인 `<style>` 태그 모두에서 CSS를 파싱하여 `color: #008000` 등 초록 계열 색상을 가진 charshape 클래스를 `green_charshapes` 집합으로 수집
  - `get_row_cells()` 내부 함수: `<p>` 태그 내 `<span>` 자식을 순회하며 초록 charshape 클래스 여부를 확인, 해당 텍스트를 `{{green:text}}` 마커로 래핑
  - `_clean_meal_content()`: `{{green:...}}` 마커를 `\x00GREENn\x00` 플레이스홀더로 임시 치환하여 정리 과정에서 보호. 마커 내부 텍스트도 알레르기 번호/괄호 제거 등 정리 후 복원
  - `parse_hwp_meal()`: hwp5html 임시 디렉토리에서 `styles.css` 파일을 읽어 `_parse_meal_html()`에 전달 (디렉토리 삭제 전에 수행)

### 프론트엔드 (view.ts)
- **`src/app/page.note.meal/view.ts`**
  - `formatMealContent(content: string): string` 메서드 추가: `{{green:text}}` 마커를 `<span class="green-text">text</span>` HTML로 변환. XSS 방지를 위해 마커 외부 텍스트는 `&`, `<`, `>` 이스케이프 처리, 줄바꿈은 `<br>`로 변환

### 템플릿 (view.pug)
- **`src/app/page.note.meal/view.pug`**
  - `.meal-content` 요소: 텍스트 보간(`{{ meal.content }}`)에서 `[innerHTML]="formatMealContent(meal.content)"`로 변경하여 HTML 렌더링 활성화

### 스타일 (view.scss)
- **`src/app/page.note.meal/view.scss`**
  - `.meal-content` 내부에 `::ng-deep .green-text { color: #008000; font-weight: 600; }` 스타일 추가
