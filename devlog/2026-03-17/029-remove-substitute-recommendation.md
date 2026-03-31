# 알레르기 패널에서 AI 대체 식품 추천 기능 제거

- **ID**: 029
- **날짜**: 2026-03-17
- **유형**: 기능 제거

## 작업 요약
component.header의 알레르기 패널에서 AI 대체 식품 추천 기능을 완전히 제거. view.pug, view.ts, api.py, view.scss 4개 파일에서 관련 코드 일괄 삭제.

## 변경 파일 목록
### component.header/view.pug
- `.substitute-section` 블록 전체 제거 (버튼, 로딩, 결과 목록 포함)

### component.header/view.ts
- 변수 제거: `substituteLoading`, `substituteResults`
- 메서드 제거: `formatMarkdown()`, `alertKey()`, `getSubstitute()`, `hasSubstitute()`, `getSubstituteList()`, `isSubstituteLoading()`

### component.header/api.py
- `get_substitute_recommendation()` 함수 전체 제거 (Gemini AI 호출 로직 포함)

### component.header/view.scss
- 스타일 제거: `.substitute-section`, `.btn-substitute`, `.substitute-list`, `.substitute-title`, `.substitute-empty`, `.substitute-item`, `.sub-row`, `.sub-original`, `.sub-arrow`, `.sub-substitute`, `.sub-reason`
