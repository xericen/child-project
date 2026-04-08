# 부모 페이지 저녁메뉴 추천 빈 응답 문제 수정

- **ID**: 001
- **날짜**: 2026-04-06
- **유형**: 버그 수정

## 작업 요약
부모(parent) 역할 사용자가 저녁메뉴 추천 버튼 클릭 시 아무 값도 표시되지 않는 문제 수정. 백엔드 에러 핸들링 부재 및 ThreadPoolExecutor wiz 컨텍스트 이슈를 해결.

## 변경 파일 목록

### 백엔드 (api.py)
- `src/app/page.note.today/api.py`
  - `recommend_dinner()`: ResponseException을 제외한 모든 예외를 catch하는 wrapper try/except 추가 → 미처리 예외 시 500 에러 메시지 반환
  - `_recommend_dinner_impl()`: 외부 ThreadPoolExecutor를 순차 호출로 교체 → exec() 환경에서 wiz 컨텍스트 스레드 안전성 문제 해결
  - Gemini AI 호출 실패 시 빈 응답 대신 사용자 안내 메시지(tip) 설정 및 에러 로깅 추가

### 프론트엔드 (view.ts)
- `src/app/page.note.today/view.ts`
  - `recommendDinner()`: try/catch/finally 패턴으로 리팩토링 → wiz.call 실패, 네트워크 에러 등 모든 경우에 dinnerLoading=false 보장
  - 500 에러 시 `res.data.message` 필드도 확인하여 서버 에러 메시지 표시
