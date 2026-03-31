# AI 응답 마크다운 렌더링 (볼드체/이탤릭)

- **ID**: 026
- **날짜**: 2026-03-17
- **유형**: 기능 추가

## 작업 요약
AI 응답에 포함된 마크다운(**bold**, *italic*)이 plain text로 출력되던 문제 수정. 각 컴포넌트에 `formatMarkdown()` 메서드 추가하여 `**text**` → `<b>text</b>`, `*text*` → `<i>text</i>`, `\n` → `<br>` 변환. HTML 이스케이프 처리 후 마크다운 변환하여 XSS 방지.

## 변경 파일 목록
### component.header
- **view.ts**: `formatMarkdown()` 메서드 추가
- **view.pug**: `.sub-reason`에 `[innerHTML]="formatMarkdown(rec.reason)"` 적용

### page.note.today
- **view.ts**: `formatMarkdown()` 메서드 추가
- **view.pug**: `.dinner-text`에 `[innerHTML]="formatMarkdown(dinnerRecommendation)"` 적용

### page.note.activity
- **view.ts**: `formatMarkdown()` 메서드 추가
- **view.pug**: `.activity-desc`에 `[innerHTML]="formatMarkdown(act.description)"` 적용
