# 아이체크 (ChildCheck)

어린이집 학부모·교사·원장을 위한 영양 관리 및 알림장 웹 서비스입니다.

## 주요 기능

### 식단 관리
- **오늘의 식단** — 오전간식 / 점심 / 오후간식 확인
- **연령별 메뉴 분기** — 1~2세 / 3~5세에 맞는 메뉴 자동 표시 (백김치↔배추김치, 대체메뉴 등)
- **알레르기 경고** — 자녀 알레르기에 해당하는 메뉴 자동 감지 및 경고

### 영양 분석
- **식약처 API 기반** — 실제 영양 데이터 (6단계 검색: DB캐시 → 로컬DB → 식약처API → 메뉴젠API → AI매칭 → AI추정)
- **연령별 1인분 스케일링** — per-100g 데이터를 보건복지부 어린이집 급식관리지침 기준 아동 1인분으로 변환
- **DB 열량/단백질 보정** — 영양사 입력값(DB) 기준으로 API 결과를 비례 스케일링
- **영양소 목표 대비 분석** — 칼로리, 단백질, 지방, 탄수화물, 칼슘, 철분 부족/적정/초과 판정
- **월간 영양 대시보드** — 일별 칼로리 추이, 영양소 달성률, 부족 영양소 분석

### 저녁 추천 (AI)
- 어린이집 식사 영양 분석 기반 부족 영양소 보충 저녁 메뉴 추천
- 알레르기 회피, 연령 맞춤 칼로리 고려

### 알림장
- 활동 기록, 식사 사진, 건강 체크
- 승인 워크플로

### 기타
- PWA 지원 (모바일 설치)
- 서버(어린이집) 생성/참여
- 회원가입, 비밀번호 찾기

## 기술 스택

| 구분 | 기술 |
|------|------|
| 프레임워크 | WIZ Framework |
| 프론트엔드 | Angular + Pug + Tailwind CSS |
| 백엔드 | Python (WIZ exec 환경) |
| DB | MySQL (Peewee ORM) |
| AI | Google Gemini API |
| 외부 API | 식약처 식품영양성분 DB API |

## 환경 변수

| 변수 | 설명 |
|------|------|
| `FOOD_SAFETY_API_KEY` | 식약처 식품영양성분 API 인증키 |
| `GEMINI_API_KEY` | Google Gemini API 키 |

## 프로젝트 구조

```
src/
├── app/                          # 페이지 및 컴포넌트
│   ├── page.main/                # 메인 페이지
│   ├── page.note.today/          # 오늘의 식단 + 저녁 추천
│   ├── page.note.meal/           # 식단 관리 (월간 캘린더, 통계)
│   ├── page.note.meal.nutrition/ # 영양 분석 대시보드
│   ├── page.note.activity/       # 활동 기록
│   ├── page.note.photo/          # 사진 기록
│   ├── page.note.approve/        # 알림장 승인
│   ├── page.childcheck/          # 건강 체크
│   ├── page.myinfo/              # 내 정보 관리
│   ├── page.server/              # 서버(어린이집) 관리
│   └── ...
├── model/
│   ├── nutrition_api.py          # 영양 검색 엔진 (6단계 검색 + 1인분 스케일링)
│   ├── gemini.py                 # Gemini AI 모델
│   └── db/                       # DB 모델 (Peewee ORM)
├── portal/                       # 공유 패키지 (season 등)
└── angular/                      # Angular 빌드 설정
```

## 빌드 및 실행

```bash
# 프로젝트 빌드
cd /opt/app && wiz project build --project=main

# 클린 빌드 (새 API 함수 추가 시)
cd /opt/app && wiz project build --project=main --clean
```
