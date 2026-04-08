# child — 어린이집 알림장

어린이집 학부모·교사·원장을 위한 **식단 관리, 영양 분석, AI 저녁 추천, 알림장** 웹 서비스입니다.
PWA를 지원하여 모바일에서 앱처럼 설치·사용할 수 있습니다.

---

## 주요 기능

### 🍱 식단 관리
- **오늘의 식단** — 오전간식 / 점심 / 오후간식 확인 (학부모·교사 공통)
- **연령별 메뉴 분기** — 1~2세 / 3~5세에 맞는 메뉴 자동 표시 (백김치↔배추김치 등)
- **대체식 선택** — 교사/원장이 날짜별로 대체 메뉴를 선택하면 학부모에게 자동 반영
- **알레르기 경고** — 자녀 알레르기에 해당하는 메뉴 자동 감지 및 경고 (AI 기반 성분 분석)
- **식단표 업로드** — HWP 파일 파싱으로 월간 식단 일괄 등록
- **식단 사진** — 카드형 UI로 식사 사진 업로드·관리

### 📊 영양 분석
- **6단계 검색 파이프라인** — DB 캐시 → 로컬 DB(55만건) → 식약처 API → 메뉴젠 API → AI 매칭 → AI 추정
- **연령별 1인분 스케일링** — per-100g 데이터를 보건복지부 급식관리지침 기준 아동 1인분으로 변환
- **영양사 입력값 보정** — DB 열량/단백질 기준으로 API 결과를 비례 스케일링
- **6대 영양소 분석** — 칼로리, 단백질, 지방, 탄수화물, 칼슘, 철분 부족/적정/초과 판정
- **월간 영양 대시보드** — 일별 칼로리 추이 차트, 영양소 달성률, 부족 영양소 분석

### 🤖 AI 저녁 추천
- 어린이집 **실제 제공 메뉴** 기반 영양 분석 (교사 대체식 선택 반영)
- 부족 영양소 보충 저녁 메뉴 2~3개 추천
- 알레르기 회피, 자녀 연령·발달단계 맞춤

### 📋 알림장
- 활동 기록 (교사 작성)
- 식사 사진 (공용/개인, 3식 분류)
- 건강 체크
- 원장 승인 워크플로

### 👥 서버(어린이집) 시스템
- 서버 생성 (원장) / 서버 코드로 참여 (교사·학부모)
- 기기별 최근 참여 서버 기억 (localStorage)
- 역할별 권한 분리 (학부모 / 교사 / 원장)
- QR 코드 기반 서버 코드 공유

### 기타
- **PWA** — 홈 화면 설치, 오프라인 폴백, 푸시 알림
- **이메일 인증** — 회원가입 시 6자리 인증코드 (SMTP)
- **비밀번호 찾기** — 이메일 인증 후 재설정

---

## 기술 스택

| 구분 | 기술 |
|------|------|
| 프레임워크 | WIZ Framework |
| 프론트엔드 | Angular 18 + Pug + Tailwind CSS |
| 백엔드 | Python (WIZ exec 환경) |
| DB | MySQL (Peewee ORM) |
| AI | Google Gemini API |
| 영양 데이터 | 식약처 식품영양성분 DB API + 국가표준식품성분 로컬 DB |
| 푸시 알림 | Web Push (Service Worker) |
| 이메일 | SMTP (Gmail) |

---

## 환경 변수

`.env` 파일 또는 시스템 환경변수로 설정합니다.

| 변수 | 설명 |
|------|------|
| `DB_HOST` | MySQL 호스트 (기본: `127.0.0.1`) |
| `DB_PORT` | MySQL 포트 (기본: `3306`) |
| `DB_USER` | MySQL 사용자 |
| `DB_PASSWORD` | MySQL 비밀번호 |
| `FOOD_SAFETY_API_KEY` | 식약처 식품영양성분 API 인증키 |
| `SMTP_HOST` | SMTP 서버 (기본: `smtp.gmail.com`) |
| `SMTP_PORT` | SMTP 포트 (기본: `587`) |
| `SMTP_SENDER` | 발신 이메일 주소 |
| `SMTP_PASSWORD` | SMTP 비밀번호 (앱 비밀번호) |

> Gemini API 키는 `config/ai.py`에서 설정합니다.

---

## 프로젝트 구조

```
src/
├── app/                              # 페이지 및 컴포넌트 (20+ 페이지)
│   ├── page.main/                    # 로그인 / 메인
│   ├── page.signup/                  # 회원가입 (역할 토글 선택)
│   ├── page.forgot/                  # 비밀번호 찾기
│   ├── page.server.create/           # 서버(어린이집) 생성
│   ├── page.server.join/             # 서버 참여 (코드 입력, 최근 서버 기억)
│   ├── page.childcheck/              # 자녀 건강 체크
│   ├── page.note/                    # 알림장 레이아웃
│   ├── page.note.today/              # 오늘의 식단 + AI 저녁 추천
│   ├── page.note.meal/               # 식단표 관리 (캘린더 + 사진 업로드)
│   ├── page.note.meal.nutrition/     # 영양 분석 대시보드
│   ├── page.note.activity/           # 활동 기록
│   ├── page.note.photo/              # 사진 관리 (카드형 UI)
│   ├── page.note.approve/            # 원장 승인
│   ├── page.note.profile/            # 프로필
│   ├── page.myinfo/                  # 내 정보 관리
│   ├── page.pwa.install/             # PWA 설치 안내
│   ├── layout.navbar/                # 네비게이션 바 레이아웃
│   └── component.header/             # 헤더 컴포넌트
├── model/
│   ├── nutrition_api.py              # 영양 검색 엔진 (6단계 파이프라인)
│   ├── gemini.py                     # Gemini AI 헬퍼
│   ├── mailer.py                     # 이메일 발송
│   ├── push.py                       # 푸시 알림
│   ├── struct.py                     # Struct 진입점
│   └── db/
│       ├── login_db/                 # 인증 DB (users, servers, server_members)
│       └── childcheck/               # 서비스 DB (meals, children, photos, nutrition 등 11테이블)
├── controller/                       # 인증/권한 체인 (base → user → admin)
├── portal/                           # 공유 패키지 (season)
├── angular/                          # Angular 빌드 설정
└── assets/                           # 정적 자산 (PWA manifest, 아이콘)
```

---

## DB 스키마 개요

### login_db (인증)
- `users` — 사용자 (이메일, 비밀번호, 역할)
- `servers` — 어린이집 서버
- `server_members` — 서버-사용자 매핑

### childcheck (서비스)
- `children` — 자녀 정보
- `child_allergies` — 자녀 알레르기
- `allergy_categories` — 알레르기 카테고리
- `meals` — 식단 (연령별 칼로리/단백질, 메뉴 텍스트)
- `meal_substitute_selections` — 교사 대체식 선택 이력
- `photos` / `photo_comments` — 식단 사진 및 댓글
- `nutrition_foods` — 국가표준식품성분 (55만건 로컬 미러)
- `nutrition_mapping` — 메뉴명→영양소 매핑 캐시
- `notifications` — 알림
- `push_subscriptions` — 푸시 구독

---

## 빌드 및 실행

```bash
# 프로젝트 빌드
cd /opt/app && wiz project build --project=main

# 클린 빌드 (새 API 함수 추가/삭제 시)
cd /opt/app && wiz project build --project=main --clean
```
