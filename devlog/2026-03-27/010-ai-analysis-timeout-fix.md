# AI 분석 타임아웃(readyState:0) 해결

- **ID**: 010
- **날짜**: 2026-03-27
- **유형**: 버그 수정

## 작업 요약
`loadAiAnalysis()`의 `wiz.call()` → `fetch()` + `AbortController(120s timeout)`으로 변경. 장시간 소요되는 AI 분석 API 호출이 브라우저 기본 타임아웃에 의해 중단되는 문제 해결. AbortError 시 별도 에러 메시지 표시.

## 변경 파일 목록
- `src/app/page.note.meal/view.ts`: loadAiAnalysis — wiz.call → fetch+AbortController
- `src/app/page.note.meal/view.pug`: AI 로딩 메시지에 "(최대 2분 소요)" 안내 추가
