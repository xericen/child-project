# Gemini API 연동 기반 환경 구축

- **ID**: 005
- **날짜**: 2026-03-17
- **유형**: 기능 추가

## 작업 요약
Google Gemini AI API 연동을 위한 기반 환경 구축. `google-genai` 패키지 설치, API 키 설정(`config/ai.py`), 공통 유틸리티 모델(`src/model/gemini.py`)을 작성. 모델은 `gemini-2.5-flash`를 사용.

## 변경 파일 목록
### 패키지
- `google-genai==1.67.0` 설치

### Config
- `config/ai.py`: 신규 생성 — Gemini API 키 및 모델명 설정

### Model
- `src/model/gemini.py`: 신규 생성 — GeminiHelper 클래스 (ask/ask_json 메서드)
