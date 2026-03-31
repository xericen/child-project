# AI 연결 상태 점검

- **ID**: 008
- **날짜**: 2026-03-17
- **유형**: 설정 변경

## 작업 요약
Gemini API 연결 상태를 점검한 결과 API 키, 모델명(gemini-2.5-flash) 설정은 정상. 무료 쿼터(일 20회) 초과로 429 RESOURCE_EXHAUSTED 에러 발생 중. 유료 플랜 전환이 필요.

## 확인 사항
- `config/ai.py`: API 키, 모델명 정상
- `src/model/gemini.py`: genai.Client 초기화, ask/ask_json 함수 정상
- 모델 목록 조회 성공, gemini-2.5-flash 사용 가능 확인
- 에러: `429 RESOURCE_EXHAUSTED` — 무료 쿼터(20 req/day) 초과
