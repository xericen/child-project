# 🌱 ChildNote — 어린이집/유치원 통합 알림장 서비스

> **부모, 교사, 원장을 하나로 잇는 스마트 케어 플랫폼**
> 식단·알레르기·활동·사진을 한 곳에서, AI 영양 분석과 자동 알림까지.

[![Stack](https://img.shields.io/badge/Backend-Python%20%7C%20Flask-3776AB?logo=python&logoColor=white)]()
[![Stack](https://img.shields.io/badge/Frontend-Angular%2017-DD0031?logo=angular&logoColor=white)]()
[![Stack](https://img.shields.io/badge/DB-MySQL-4479A1?logo=mysql&logoColor=white)]()
[![Stack](https://img.shields.io/badge/AI-Gemini%202.5-4285F4?logo=google&logoColor=white)]()
[![Stack](https://img.shields.io/badge/PWA-Ready-5A0FC8?logo=pwa&logoColor=white)]()

---

## 📖 프로젝트 소개

**ChildNote**는 어린이집·유치원의 일상 운영을 디지털화하는 **올인원 알림장 서비스**입니다.
종이 알림장과 흩어진 SNS 공지로 인한 정보 누락, 식단 알레르기 사고 위험, 비효율적인 학부모 소통 문제를 해결하기 위해 설계되었습니다.

### 🎯 해결하는 문제

| 기존 문제 | ChildNote의 해결책 |
|---|---|
| 종이 알림장 분실, 전달 누락 | 모바일 PWA로 실시간 알림 |
| 식단표에서 우리 아이 알레르기 식자재 일일이 확인 | **자동 매칭 + 빨간 테두리 강조 표시** |
| 영양 균형이 한눈에 안 보임 | **Gemini AI 기반 일/월간 영양 분석 리포트** |
| 교사 업무 부담 (수기 기록, 사진 정리) | 역할별 권한 분리 + 사진 일괄 업로드 |
| 등하원·결석 정보 단방향 전달 | 학부모↔교사 양방향 컨펌 시스템 |

---

## ✨ 주요 기능

### 👨‍👩‍👧 학부모

- **오늘의 식단 한눈에 보기** — 우리 아이 알레르기 식재료가 포함된 메뉴는 자동으로 빨간 테두리 강조
- **AI 영양 분석** — Gemini 기반으로 칼로리·5대 영양소·식단 균형을 일/월 단위로 자동 리포트
- **활동·사진 피드** — 교사가 올린 활동 기록과 사진을 타임라인으로 확인
- **자녀 결석/조퇴 신청** — 원클릭 신청, 교사 승인 시 푸시 알림

### 🧑‍🏫 교사

- **식단표 OCR 업로드** — 월간 식단표 이미지를 업로드하면 자동 파싱 + 알레르기 매핑
- **사진 업로드** — 다중 업로드, 자동 압축, 썸네일 생성
- **출결·활동 일지 작성** — 자녀별 일지를 모바일에서 즉시 작성/공유

### 🏫 원장

- **다기관 운영** — 여러 어린이집/지점을 하나의 계정으로 관리
- **승인 워크플로** — 회원가입 승인, 교사 권한 부여
- **운영 대시보드** — 식단·출결·알레르기 통계

---

## 🏗 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                  Client (PWA — Angular 17)                  │
│  Mobile-first UI · Service Worker · Push Notifications      │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS / WebSocket
┌────────────────────────▼────────────────────────────────────┐
│                  WIZ Framework (Flask 기반)                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Controller 체인: base → user → admin (인증/권한)     │   │
│  │ App API (api.py)  ·  REST Route  ·  WebSocket        │   │
│  └──────────────────────────────────────────────────────┘   │
└──────┬──────────────────┬──────────────────┬────────────────┘
       │                  │                  │
       ▼                  ▼                  ▼
  ┌─────────┐      ┌──────────────┐    ┌──────────────┐
  │  MySQL  │      │  Gemini AI   │    │  Push (FCM)  │
  │ login_db│      │ (영양 분석)  │    │ (알림 발송)  │
  │childcheck│      │ (식단 OCR)   │    │              │
  └─────────┘      └──────────────┘    └──────────────┘
```

### 데이터 계층

| Database | 역할 |
|---|---|
| `login_db` | 사용자 계정, 세션, 기관(server) 멤버십 |
| `childcheck` | 자녀 정보, 식단, 알레르기, 활동, 사진, 알림 |

---

## 🛠 기술 스택

### Backend
- **Python 3.11+** · **Flask** (WIZ Framework 기반)
- **Peewee ORM** — MySQL 연동
- **Google Gemini 2.5 Flash** — 식단 OCR 및 영양 분석
- **APScheduler** — 알레르기 알림 자동 발송
- **Web Push (VAPID)** — PWA 푸시 알림

### Frontend
- **Angular 17** (Standalone Components)
- **Pug** — 템플릿 엔진
- **Tailwind CSS** + **SCSS**
- **PWA** — Service Worker, manifest, 오프라인 캐시

### Infrastructure
- **MySQL 8** · **Nginx** · **Gunicorn**
- **WIZ Framework** ([Season WIZ](https://github.com/season-framework/wiz)) — App-centric 풀스택 프레임워크

---

## 📁 프로젝트 구조

```
project/main/
├── config/
│   ├── database.py          # DB 접속 (MySQL 멀티 namespace)
│   ├── ai.py                # Gemini API 설정
│   ├── push.py              # Web Push (VAPID)
│   └── season.py            # 인증/세션 설정
│
├── src/
│   ├── app/                 # Angular 페이지/레이아웃
│   │   ├── page.main/       # 로그인·메인
│   │   ├── page.signup/     # 회원가입
│   │   ├── page.note/       # 알림장 허브
│   │   ├── page.note.today/ # 오늘의 식단 (알레르기 강조)
│   │   ├── page.note.meal/  # 월간 식단표
│   │   ├── page.note.meal.nutrition/  # AI 영양 분석
│   │   ├── page.note.photo/ # 사진 피드
│   │   ├── page.note.activity/        # 활동 일지
│   │   ├── page.note.profile/         # 자녀 프로필
│   │   ├── page.childcheck/ # 출결 관리
│   │   ├── page.server/     # 기관 관리 (원장)
│   │   └── layout.navbar/   # 공통 네비게이션
│   │
│   ├── controller/          # 인증/권한 체인 (base/user/admin)
│   ├── model/               # 도메인 Struct (비즈니스 로직)
│   ├── route/               # REST API 엔드포인트
│   │   └── api.scheduler/   # 자동 알림 스케줄러
│   └── portal/season/       # WIZ 인증 패키지
│
├── data/
│   └── nutrition_normalization_rules.json  # 식단명 정규화 규칙
│
└── devlog/                  # 일자별 개발 이력 (작업 로그)
```

---

## 🚀 실행 방법

### 1. 사전 요구사항

```bash
# 시스템 패키지 (SAML/PWA 빌드용)
apt install pkg-config libxml2-dev libxmlsec1-dev libxmlsec1-openssl

# Python 3.11+
pip install -r requirements.txt    # peewee, pymysql, bcrypt, flask 등

# Node.js 18+ (Angular 빌드)
npm install
```

### 2. 환경 변수 설정

`project/main/.env` 파일을 생성합니다:

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password

GEMINI_API_KEY=your_gemini_api_key
VAPID_PUBLIC_KEY=...
VAPID_PRIVATE_KEY=...
```

### 3. 데이터베이스 초기화

```sql
CREATE DATABASE login_db    DEFAULT CHARACTER SET utf8mb4;
CREATE DATABASE childcheck  DEFAULT CHARACTER SET utf8mb4;
```

스키마는 첫 실행 시 ORM이 자동 생성합니다.

### 4. 빌드 & 실행

```bash
# WIZ 프로젝트 빌드 (Angular + 라우팅 등록)
wiz build

# 서버 실행
wiz run    # 기본 포트 3000
```

브라우저에서 `http://localhost:3000` 접속.

---

## 🔐 사용자 권한 모델

```
┌─────────────┐
│   parent    │  자녀 정보 조회, 결석 신청, 사진/활동 열람
└─────────────┘
       │
┌─────────────┐
│   teacher   │  + 식단 업로드, 활동 작성, 사진 등록, 출결 관리
└─────────────┘
       │
┌─────────────┐
│  director   │  + 회원/교사 승인, 기관 설정, 통계 대시보드
└─────────────┘
```

권한 검증은 **Controller 계층**(`src/controller/`)에서 일괄 처리되어, 라우트별 코드 중복 없이 안전하게 제어됩니다.

---

## 🤖 AI 영양 분석 파이프라인

```
식단명 입력
    ↓
[1] 룰 기반 정규화 (data/nutrition_normalization_rules.json)
    ↓
[2] Gemini 정규화 (오타·줄임말 보정)
    ↓
[3] 식품 DB 매칭 (직접 사용)  ← 캐시 우선
    ↓
[4] Gemini 영양소 추정 (DB 미스 시)
    ↓
[5] 배식량·연령별 스케일 보정
    ↓
영양 분석 결과 (칼로리, 5대 영양소, 등급)
```

**최적화 포인트**:
- `MealNutritionCache` — 동일 식단 재분석 방지
- 월간 알레르기 매칭 결과 AI 캐시
- 식단표 업로드 후 월간/일간 프리패치

---

## 📱 PWA 지원

- **설치 가능** — 모바일 홈 화면에 앱처럼 추가
- **오프라인 캐시** — Service Worker로 식단/사진 캐싱
- **푸시 알림** — Web Push (VAPID) 기반
  - 우리 아이 알레르기 식재료 포함 식단 자동 경고
  - 활동·공지 새 글 알림
  - 출결 승인 결과 알림

---

## 🗓 개발 이력

`devlog/` 폴더에서 일자별 상세 개발 이력을 확인할 수 있습니다.
주요 마일스톤은 [`devlog.md`](devlog.md)에 한눈에 정리되어 있습니다.

### 핵심 마일스톤

- **2026-03** · 초기 인증/회원가입/역할 시스템 구축
- **2026-03** · 알림장 허브, 식단·사진·활동·프로필 페이지
- **2026-04** · 식단 OCR + Gemini 영양 분석 도입
- **2026-04** · 알레르기 자동 매칭 + 빨간 테두리 UX
- **2026-04** · 영양분석 캐시 시스템, 칼로리 정확도 개선
- **2026-04** · 식단표 업로드 속도 최적화 + 프리패치
- **2026-04** · PWA 푸시 알림, 자동 스케줄러

---

## 📊 포트폴리오

상세한 프로젝트 소개와 기술 의사결정은 [`portfolio/child_portfolio.pptx`](portfolio/child_portfolio.pptx)에서 확인할 수 있습니다 (16 slides).

---

## 📝 라이선스

이 저장소는 학습 및 포트폴리오 목적의 사이드 프로젝트입니다.
상업적 사용 전 별도 문의 부탁드립니다.

---

## 👤 Author

**xericen** · [GitHub](https://github.com/xericen)

> 작은 문제 하나라도 진심으로 해결하려는 자세로 만들고 있습니다.
