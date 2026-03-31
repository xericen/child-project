# 통계 페이지 "AI 분석 중" 멈춤 버그 수정

- **ID**: 008
- **날짜**: 2026-03-27
- **유형**: 버그 수정

## 작업 요약
`page.note.meal`의 `goStats()`, `refreshAiAnalysis()`, `reloadStats()`에 try/catch/finally를 추가하여, `loadAiAnalysis()` 등에서 예외 발생 시에도 `aiLoading=false`가 보장되도록 수정. 에러 발생 시 사용자에게 메시지를 표시하고 "다시 시도" 버튼 제공.

## 변경 파일 목록

### Frontend
- `src/app/page.note.meal/view.ts`
  - `aiError` 변수 추가
  - `goStats()`: try/catch/finally 래핑, finally에서 statsLoading/aiLoading 확실히 false
  - `loadAiAnalysis()`: try/catch 추가, 실패 시 aiError 설정
  - `refreshAiAnalysis()`: try/catch/finally 추가
  - `reloadStats()`: try/catch/finally 추가
- `src/app/page.note.meal/view.pug`
  - AI 에러 메시지 표시 영역 추가 (`aiError` 변수 바인딩 + "다시 시도" 버튼)
