# AI 모델 통일 확인 (gemini-2.0-flash-lite)

- **ID**: 027
- **날짜**: 2026-03-17
- **유형**: 설정 변경

## 작업 요약
모든 AI 호출이 동일 모델을 사용하는지 확인. config/ai.py에 gemini-2.0-flash-lite가 설정되어 있고, src/model/gemini.py가 config에서 동적으로 모델명을 로드하며, 모든 AI 호출(header, today, activity)이 wiz.model("gemini")를 사용하여 이미 통일됨. 코드 변경 불필요.

## 변경 파일 목록
없음 (확인만 수행)
