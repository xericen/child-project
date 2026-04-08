# 버그 수정: 알레르기 음식명 표시, 교사뷰 연결메뉴 분리, 저녁추천 에러 상세 + 콘솔 로깅

- **ID**: 006
- **날짜**: 2026-04-07
- **유형**: 버그 수정

## 작업 요약
1. 오늘의 식단(today) 알레르기 경고에 음식명이 누락되던 문제 수정 (알레르겐 이름만 → "치즈죽(우유)" 형태)
2. 식단표(meal) 교사/원장 뷰에서 백김치배추김치가 분리 표시되지 않던 문제 수정 (parseMealLines에 연결메뉴 분리 추가)
3. 저녁 추천 Gemini API 에러가 프론트엔드에 전달되지 않던 문제 수정 (error, traceback 필드 추가)
4. 프론트엔드 콘솔에 Stage1~3 음식별 상세 로깅 추가
5. dish_allergies의 green 마커가 음식명에 남아있던 문제 수정

## 변경 파일 목록

### 백엔드 (page.note.today/api.py)
- `get_today_menu()`: `allergy_dishes` 딕셔너리 추가 — dish_allergies 정밀 매칭에서 음식명+알레르겐 쌍을 수집하여 응답에 포함
- `allergy_dishes` 내 dish_name에서 `{{green:...}}` 마커 제거 (re.sub)
- `_recommend_dinner_impl()` Stage3: Gemini 에러 시 `error`, `traceback` 필드를 stage3에 추가하여 프론트엔드로 전달

### 프론트엔드 (page.note.today/view.ts)
- `allergyDishes` 변수 추가, `loadData()`에서 `allergy_dishes` 저장
- `getAllergyText()`: `allergy_dishes`가 있으면 "음식명(알레르겐)" 형식으로 표시
- `fixGreenAndScaling()`: Stage1 음식별 칼로리·영양소·소스 상세 로깅, Stage3 에러/traceback 콘솔 출력

### 프론트엔드 (page.note.meal/view.ts)
- `parseMealLines()`: 교사/원장 role일 때 연결 메뉴(백김치배추김치)를 "백김치(1~2세)\n배추김치(3~5세)"로 분리 표시

## 검증 결과
- curl로 교사 toggle_substitute on/off → DB 기록 확인
- 학부모(1~2세) 점심: toggle on→가자미구이, toggle off→가자미조림
- 학부모(1~2세) 백김치, (3~5세) 배추김치 정상 분기
- 알레르기: 치즈죽(우유), 근대청국장국(돼지고기) 정상 매칭
- 저녁추천: Gemini API key expired 에러가 stage3.error로 프론트엔드에 전달됨
