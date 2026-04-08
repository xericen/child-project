# 저녁추천/영양분석 — 실제 제공 메뉴 기반 분석

- **ID**: 005
- **날짜**: 2026-04-07
- **유형**: 기능 수정

## 작업 요약
저녁추천의 영양분석 파이프라인 입력을 기존 `_adapt_content_for_age`에서 `_apply_parent_content`로 교체하여, 교사가 선택한 실제 제공 메뉴 기반으로 영양분석이 수행되도록 했다.

## 변경 파일 목록
### page.note.today/api.py
- `_recommend_dinner_impl()`: `_adapt_content_for_age()` → `_apply_parent_content()` 교체
  - 교사가 대체식 선택(☑) 시 대체 메뉴로 분석
  - 미선택 시 원본 메뉴로 분석
  - 연결 메뉴(백김치/배추김치)도 자녀 연령에 맞는 것만 분석 대상
