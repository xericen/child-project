# 알레르기 알림 '기타' 타입 매칭 수정 + childcheck/반삭제 검증

- **ID**: 001
- **날짜**: 2026-03-26
- **유형**: 버그 수정

## 작업 요약
이구름(child_id=17)의 알레르기가 `allergy_type='기타', other_detail='닭고기'`로 저장되어 있었으나,
스케줄러의 `check_allergies()`에서 `ALLERGY_TYPE_TO_NUMBERS.get('기타', [])`로 빈 리스트가 반환되어 매칭 실패.
`other_detail` 텍스트도 매핑에서 검색하도록 수정하여 닭불고기(닭고기) 매칭 성공.
childcheck 플로우 검증 완료, 반 삭제(사람반) 정상 동작 확인.

## 변경 파일 목록

### `src/route/api.scheduler/controller.py`
- `check_allergies()` 내 아이 알레르기 번호 수집 로직:
  - `allergy_type == '기타'`일 때 `other_detail` 텍스트를 `ALLERGY_TYPE_TO_NUMBERS`에서 검색
  - `other_detail`에 콤마/공백 구분 여러 알레르기 기재 시 각각 분리하여 매핑

### 검증 결과
- 수동 API 호출: 이구름 → 닭불고기(닭고기) 매칭 성공
- 알림 4건 발송: 부모(user53) + 교직원(user49,51,55)
- 반 삭제(사람반): 교사0, 학생1, 학부모1 정상 삭제
- childcheck 플로우: 신규/기존 학부모 경로 정상
