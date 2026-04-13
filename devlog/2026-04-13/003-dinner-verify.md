# 저녁 추천 결과 검증 로직 추가

- **ID**: 003
- **날짜**: 2026-04-13
- **유형**: 기능 추가

## 작업 요약
Stage 3 AI 저녁 추천 응답에 대해 검증 단계를 추가. 개별 메뉴 칼로리가 연령 기준 합리 범위(1~2세: 30~350kcal, 3~5세: 40~500kcal) 내인지, 총 칼로리가 부족분의 0.5~1.5배 범위 내인지 확인. 검증 실패 시 보정 프롬프트로 1회 재시도 후 `verified: true/false` 필드를 stage3 응답에 포함.

## 변경 파일 목록

### 수정
- `src/app/page.note.today/api.py`:
  - `_verify_dinner()` 내부 함수 추가 - 개별 메뉴 칼로리 범위 + 총 칼로리 비율 검증
  - Stage 3 Gemini 호출 후 검증 → 실패 시 이슈 포함 보정 프롬프트로 재시도 (최대 1회)
  - `stage3['verified']` (true/false) 필드 추가
  - `stage3['verification_issues']` 배열 (실패 시 구체적 사유)
