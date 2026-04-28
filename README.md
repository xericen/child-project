# 🧒 child — 어린이집 알림장 PWA

어린이집 학부모 · 교사 · 원장을 위한 **식단 관리 · 영양 분석 · AI 저녁 추천 · 알림장** 웹 서비스입니다.  
PWA를 지원하여 모바일에서 앱처럼 설치 · 사용할 수 있습니다.

---

## 📋 목차

- [주요 기능](#주요-기능)
- [아키텍처](#아키텍처)
- [기술 스택](#기술-스택)
- [프로젝트 구조](#프로젝트-구조)
- [DB 스키마](#db-스키마)
- [영양 분석 파이프라인](#영양-분석-파이프라인)
- [알레르기 감지 시스템](#알레르기-감지-시스템)
- [설치 및 환경 설정](#설치-및-환경-설정)
- [빌드 및 실행](#빌드-및-실행)
- [역할별 기능 매트릭스](#역할별-기능-매트릭스)

---

## 주요 기능

### 🍱 식단 관리

| 기능 | 설명 |
|------|------|
| 오늘의 식단 | 오전간식 / 점심 / 오후간식을 **타임라인 UI**로 확인 (학부모·교사 공통) |
| 연령별 메뉴 분기 | 1~2세 / 3~5세에 맞는 메뉴 자동 표시 (백김치↔배추김치 등) |
| 대체식 선택 | 교사/원장이 날짜별로 대체 메뉴를 선택하면 학부모에게 자동 반영 |
| 알레르기 경고 | 표준 19종 + 기타(커스텀) 알레르기 자동 감지, **빨간 테두리 카드 강조** + 인라인 경고 |
| 식단표 업로드 | HWP 파일 파싱으로 월간 식단 일괄 등록 (프로그레스바 UX) |
| 식단 캘린더 | 월별 캘린더 뷰 + 날짜별 타임라인 상세 보기 |
| 식단 사진 | 카드형 UI로 식사 사진 업로드·관리 (공용/개인, 3식 분류) |

### 📊 영양 분석

| 기능 | 설명 |
|------|------|
| 하이브리드 분석 | 로컬 식품DB(55만건) → BASIC_INGREDIENTS → 식품군 표준값 순서로 매칭, API/AI 미호출로 결정적 결과 보장 |
| 식품군×제공횟수 | 식약처 가이드라인(2013) 기반 연령별 제공횟수로 개별 메뉴 칼로리 계산 |
| DB 기준 비례 보정 | 총 칼로리/단백질은 식단표 DB 등록값 사용, 개별 아이템은 비례 스케일 |
| 6대 영양소 분석 | 칼로리 · 단백질 · 지방 · 탄수화물 · 칼슘 · 철분 부족/적정/초과 판정 |
| 가이드라인 JSON | `data/nutrition_guideline.json`에 기준 데이터 외부화 |
| 월간 영양 대시보드 | 일별 칼로리 추이 차트, 영양소 달성률, 부족 영양소 분석 |

### 🤖 AI 저녁 추천

- 어린이집 **실제 제공 메뉴** 기반 영양 분석 (교사 대체식 선택 반영)
- 하루 전체 권장 섭취량 대비 부족 영양소 계산
- 부족 영양소를 보충하는 가정식 저녁 메뉴 2~3개 추천
- 알레르기 회피 · 자녀 연령(개월수) · 발달단계 맞춤 1인분 기준
- **추천 결과 검증**: 개별 메뉴 칼로리 범위(1~2세 30~350 / 3~5세 40~500kcal) + 총 칼로리가 부족분의 0.5~1.5배인지 확인, 실패 시 1회 자동 재시도
- 칼로리 프로그레스 링으로 하루 목표 대비 현재 섭취량 시각화

### 🔔 알레르기 감지 시스템

| 감지 방식 | 설명 |
|-----------|------|
| 표준 19종 번호 매칭 | 식단 등록 시 음식별 알레르기 번호 ↔ 자녀 알레르기 교차 검사 |
| 키워드 직접 매칭 | 기타 알레르기 키워드가 식단명에 텍스트 포함되는지 검사 |
| 별칭(Alias) 매칭 | 돼지고기 → [돈까스, 만두, 탕수육...] 등 변형 메뉴명 매칭 |
| **월간 AI 일괄 분석** | Gemini로 이번 달 전체 음식에서 재료 수준 알레르기 감지 (월 1회 캐시) |
| 19종 자동 매핑 | 기타 알레르기가 표준 19종에 해당하면 AI로 자동 번호 매핑 |

### 📋 알림장

- 활동 기록 (교사 작성, 원장 승인 워크플로)
- 식사 사진 관리 (공용/개인 분류)
- 건강 체크 (체온, 식사량, 배변 등)
- 프로필 관리 (프로필 사진, 자녀 정보, 프로필 카드 UI)

### 👥 서버(어린이집) 시스템

- 서버 생성 (원장) / 서버 코드로 참여 (교사·학부모)
- 기기별 최근 참여 서버 기억 (localStorage)
- 역할별 권한 분리 (학부모 / 교사 / 원장)
- QR 코드 기반 서버 코드 공유
- 반(클래스) 관리 — 원장이 반 생성/삭제, 교사 배정

### 기타

- **PWA** — 홈 화면 설치, 오프라인 폴백, 푸시 알림
- **이메일 인증** — 회원가입 시 6자리 인증코드 (SMTP)
- **비밀번호 찾기** — 이메일 인증 후 재설정

---

## 아키텍처

```
클라이언트 (Angular 18 + PWA)
    ↓ HTTP / WebSocket
Controller 체인 (base → user → admin)
    ↓
App api.py (각 페이지별 백엔드 API)
    ↓
┌─────────────────────────────────────────────────────────┐
│          하이브리드 영양 분석 파이프라인                      │
│  ┌──────┐   ┌──────────┐   ┌──────────┐                │
│  │로컬DB │→ │기본재료    │→ │식품군표준  │                │
│  │55만건 │   │사전17종   │   │×제공횟수  │                │
│  └──────┘   └──────────┘   └──────────┘                │
│     ↓ source=local_db  source=basic  source=food_group │
│  ┌────────────────────────────────────────┐             │
│  │ DB 비례 보정 (cal/prot = 식단표 등록값)  │             │
│  └────────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────┘
    ↓
Model / Struct (Peewee ORM → MySQL)
```

### 영양 분석 흐름

```
오늘의 식단 요청
    → [Step 1] 메뉴 파싱 + 식품군 분류 (8개 그룹)
    → [Step 2] 하이브리드 영양값 결정
        1순위: 로컬 식품 DB (55만건) exact/LIKE 매칭 → per-100g × 배식량 스케일
        2순위: BASIC_INGREDIENTS 사전 (단순 식품)
        3순위: 식품군 표준값 × 연령별 제공횟수 (가이드라인 fallback)
    → [Step 3] DB 기준 비례 보정
        • 칼로리/단백질: 식단표 등록값 직접 사용
        • 개별 아이템: cal_ratio로 비례 스케일
    → AI 저녁 추천 (부족 영양소 기반)
        • Gemini 추천 생성 → 칼로리 범위 검증 → 실패 시 1회 재시도
```

---

## 기술 스택

| 구분 | 기술 |
|------|------|
| 프레임워크 | WIZ Framework |
| 프론트엔드 | Angular 17+ · Pug · Tailwind CSS · SCSS |
| 백엔드 | Python 3.10+ (WIZ exec 환경) |
| DB | MySQL 8.0+ (Peewee ORM) |
| AI | Google Gemini API (gemini-2.5-flash-lite) |
| 영양 데이터 | 식약처 식품영양성분 DB API + 국가표준식품성분 로컬 DB (55만건) |
| 푸시 알림 | Web Push (VAPID, Service Worker) |
| 이메일 | SMTP (Gmail 앱 비밀번호) |
| 문서 파싱 | HWP 파일 파싱 (pyhwpx, 식단표 업로드) |

---

## 프로젝트 구조

```
src/
├── app/                                  # 페이지 및 컴포넌트 (20+ 페이지)
│   ├── page.main/                        # 로그인 / 메인
│   ├── page.signup/                      # 회원가입 (역할 토글 선택)
│   ├── page.forgot/                      # 비밀번호 찾기
│   ├── page.server.create/               # 서버(어린이집) 생성
│   ├── page.server.join/                 # 서버 참여 (코드 입력, 최근 서버 기억)
│   ├── page.childcheck/                  # 건강 체크 (체온, 식사량, 배변 등)
│   ├── page.note/                        # 알림장 레이아웃 (메뉴 그리드, 프로필 바)
│   ├── page.note.today/                  # 오늘의 식단 + 영양 분석 + AI 저녁 추천
│   ├── page.note.meal/                   # 식단표 관리 (캘린더 + HWP 업로드 + 사진)
│   ├── page.note.meal.nutrition/         # 영양 분석 월간 대시보드
│   ├── page.note.activity/               # 활동 기록 (교사 작성)
│   ├── page.note.photo/                  # 사진 관리 (카드형 UI)
│   ├── page.note.approve/                # 원장 승인 워크플로
│   ├── page.note.profile/                # 프로필 카드 (역할별 뷰 분기)
│   ├── page.note.allergy/                # 알레르기 관리 (원장용 통계)
│   ├── page.myinfo/                      # 내 정보 관리
│   ├── page.pwa.install/                 # PWA 설치 안내
│   ├── layout.navbar/                    # 네비게이션 바 레이아웃
│   └── component.header/                 # 공통 헤더 컴포넌트
│
├── model/
│   ├── nutrition_api.py                  # 영양 검색 엔진 (6단계 파이프라인, 1175줄)
│   │   ├── analyze_meal_pipeline()       #   식단 → Gemini 정규화 → 병렬 검색 → 검증
│   │   ├── normalize_food_names()        #   Gemini로 식약처 검색용 이름 일괄 정규화
│   │   ├── search()                      #   단일 음식 6단계 검색
│   │   ├── search_local()                #   로컬-only 검색 (API/AI 미호출, 결정적)
│   │   ├── search_batch()                #   병렬 배치 검색
│   │   ├── scale_to_target()             #   DB 열량 기준 비례 스케일링
│   │   └── SERVING_WEIGHTS               #   연령별 1인분 중량 기준표
│   ├── gemini.py                         # Gemini AI 헬퍼
│   ├── mailer.py                         # 이메일 발송 (SMTP)
│   ├── push.py                           # 푸시 알림 (Web Push)
│   ├── struct.py                         # Struct 진입점
│   └── db/
│       ├── login_db/                     # 인증 DB
│       │   ├── users.py                  #   사용자 (이메일, 비밀번호, 역할)
│       │   ├── servers.py                #   어린이집 서버
│       │   └── server_members.py         #   서버-사용자 매핑 (역할 포함)
│       └── childcheck/                   # 서비스 DB (12 테이블)
│           ├── children.py               #   자녀 정보
│           ├── child_allergies.py         #   자녀별 알레르기 (19종+기타)
│           ├── allergy_categories.py      #   알레르기 카테고리 (주의/대체식품)
│           ├── meals.py                  #   식단 (연령별 열량/단백질, 메뉴 텍스트)
│           ├── meal_substitute_selections.py  # 교사 대체식 선택 이력
│           ├── meal_nutrition_cache.py    #   영양분석 캐시 (서버+날짜+연령그룹)
│           ├── photos.py                 #   식단 사진
│           ├── photo_comments.py          #   사진 댓글
│           ├── nutrition_foods.py         #   국가표준식품성분 (55만건 로컬 미러)
│           ├── nutrition_mapping.py       #   메뉴명→영양소 매핑 캐시
│           ├── notifications.py           #   알림
│           └── push_subscriptions.py      #   푸시 구독
│
├── controller/                           # 인증/권한 체인
│   ├── base.py                           #   세션 초기화
│   ├── user.py                           #   로그인 필수
│   └── admin.py                          #   관리자(원장) 전용
│
├── portal/                               # 공유 패키지 (season)
├── angular/                              # Angular 빌드 설정
└── assets/                               # 정적 자산 (PWA manifest, 아이콘)
```

### 데이터 파일

```
data/
└── nutrition_guideline.json              # 식약처 가이드라인 기준 데이터
```

> ⚠️ `config/`와 `data/` 디렉토리는 `.gitignore`에 포함되어 있어 Git에 커밋되지 않습니다. 아래 [설치 및 환경 설정](#설치-및-환경-설정) 섹션을 참고하여 직접 생성해야 합니다.

---

## DB 스키마

### login_db (인증)

| 테이블 | 설명 | 주요 컬럼 |
|--------|------|-----------|
| users | 사용자 계정 | email, password(bcrypt), nickname, name, role(director/teacher/parent), phone, profile_image, verified, approved |
| servers | 어린이집 서버 | server_code(8자리), name, director_name, director_id |
| server_members | 서버-사용자 매핑 | server_id, user_id, role, class_name |

### childcheck (서비스)

| 테이블 | 설명 | 주요 컬럼 |
|--------|------|-----------|
| children | 자녀 정보 | user_id, server_id, name, birthdate, gender, profile_image |
| child_allergies | 자녀 알레르기 | child_id, allergy_type(standard/other), allergy_number(1~19), other_detail |
| allergy_categories | 알레르기 카테고리 | category_name, allergy_numbers(JSON), caution_foods, substitute_foods |
| meals | 식단 데이터 | server_id, meal_date, meal_type(오전간식/점심/오후간식), content, allergy_numbers(JSON), dish_allergies(JSON), kcal, protein, kcal_35, protein_35 |
| meal_substitute_selections | 교사 대체식 선택 | meal_id, original_item, substitute_item, is_selected |
| meal_nutrition_cache | 영양분석 캐시 | server_id, meal_date, age_group(1-2/3-5), total_calories/protein/fat/carbs/calcium/iron, stage1_json |
| photos | 식단 사진 | server_id, meal_date, meal_type, photo_type(public/private), image_path, uploaded_by |
| photo_comments | 사진 댓글 | photo_id, user_id, content |
| nutrition_foods | 식품성분 DB (55만건) | food_code, food_name(index), category, calories, protein, fat, carbs, calcium, sodium, ... |
| nutrition_mapping | 영양소 매핑 캐시 | menu_name, nutrition_food_id, serving_ratio |
| notifications | 알림 | server_id, user_id, type, message |
| push_subscriptions | 푸시 구독 | user_id, endpoint, auth, p256dh |

### 테이블 자동 생성

WIZ 프레임워크는 Peewee ORM을 사용하며, 최초 실행 시 `create_table()` 메서드로 테이블이 자동 생성됩니다. 별도의 마이그레이션 스크립트는 필요하지 않습니다.

단, **nutrition_foods** 테이블(55만건)은 식약처 국가표준식품성분 데이터를 별도로 적재해야 합니다. 아래 [식품DB 초기 데이터 적재](#4-식품db-초기-데이터-적재-55만건) 참조.

---

## 영양 분석 파이프라인

### 6단계 영양소 검색 엔진 (nutrition_api.py)

음식 이름 하나를 받아 영양소 데이터를 찾는 6단계 파이프라인:

```
1. DB 캐시 (nutrition_mapping) — 이전 검색 결과 재사용
2. Gemini 정규화 — "찐고구마" → "고구마(찐것)" 등 식약처 검색명으로 변환
3. 로컬 DB (nutrition_foods, 55만건) — 국가표준식품성분 미러
4. 식약처 공공 API — 실시간 검색
5. 메뉴젠 API — 급식 관리 시스템 API
6. AI 추정 (Gemini) — 위 모든 단계에서 못 찾으면 AI가 직접 영양소 추정
```

### 하이브리드 분석 파이프라인 (_ai_analyze_all_meals)

```
[Step 1] 음식명 → 식품군 분류 (룰 기반, 8개 식품군)
   └─ 곡류 / 고기류 / 채소류 / 국류 / 김치류 / 과일류 / 우유 / 요구르트

[Step 2] 개별 영양값 결정 (하이브리드 3단계)
   ├─ 1순위: 로컬 식품 DB (nutrition_foods, 55만건) exact/LIKE 매칭
   ├─ 2순위: BASIC_INGREDIENTS 사전 (과일·우유 등 단순 식품 17종)
   └─ 3순위: 식품군 표준값 × 연령별 제공횟수 (가이드라인 fallback)
   → 각 아이템에 source 필드로 데이터 출처 표시

[Step 3] DB 기준 비례 보정
   └─ 칼로리/단백질: 식단표 등록값 사용 (확정)
   └─ 개별 아이템: cal_ratio = DB열량 / 합산열량 으로 비례 스케일
```

### 연령별 1인분 배식량 (식약처 가이드라인 2013)

| 식품군 | 1~2세 | 3~5세 | 1회 표준 칼로리 |
|--------|-------|-------|----------------|
| 곡류(밥) | 90g | 130g | 190kcal |
| 고기·생선·계란·콩류 | 30g | 45g | 50kcal |
| 채소류 | 30g | 40g | 7kcal |
| 국류 | 100ml | 140ml | 25kcal |
| 김치류 | 14g | 20g | 3kcal |
| 과일류 | 50g | 80g | 25kcal |
| 우유 | 200ml | 200ml | 120kcal |
| 요구르트 | 100g | 100g | 77kcal |

### 연령별 끼니별 제공횟수 (가이드라인 표 9)

| 식품군 | 1~2세 점심 | 1~2세 간식 | 3~5세 점심 | 3~5세 간식 |
|--------|-----------|-----------|-----------|------------|
| 곡류 | 0.7 | 0.3 | 1.0 | 0.5 |
| 고기류 | 1.5 | — | 2.0 | — |
| 채소류 | 1.5 | — | 2.5 | — |
| 국류 | 1.0 | — | 1.0 | — |
| 김치류 | 1.0 | — | 1.0 | — |
| 과일류 | — | 1.0 | — | 1.5 |
| 우유 | — | 1.0 | — | 1.0 |
| 요구르트 | — | 1.0 | — | 1.0 |

### 연령별 급식 일일 목표 (어린이집 제공분)

| 영양소 | 1~2세 | 3~5세 |
|--------|-------|-------|
| 칼로리 | 420 kcal | 640 kcal |
| 단백질 | 20 g | 12.5 g |
| 지방 | 17 g | 23 g |
| 탄수화물 | 73 g | 102 g |
| 칼슘 | 250 mg | 275 mg |
| 철분 | 3.3 mg | 4.5 mg |

---

## 알레르기 감지 시스템

### 표준 19종 알레르기

```
1.난류  2.우유  3.메밀  4.땅콩  5.대두  6.밀  7.고등어  8.게  9.새우  10.돼지고기
11.복숭아  12.토마토  13.아황산류  14.호두  15.닭고기  16.소고기  17.오징어  18.조개류  19.잣
```

### 감지 흐름

```
자녀 알레르기 데이터 수집
    ↓
┌─ 표준 19종 → 번호 매칭 (dish_allergies 교차 검사)
│
├─ 기타(커스텀) 알레르기 ─┬─ 19종 매핑 시도 (AI) → 번호 매칭
│                         └─ 19종 미해당 → 월간 AI 일괄 캐시 호출
│                                            ↓
│                              이번 달 전체 식단 음식명 추출
│                                            ↓
│                              Gemini에 1회 일괄 질문
│                              "이 음식 중 [키워드] 재료가 포함된 것은?"
│                                            ↓
│                              batch.json 캐시 저장 (월 1회)
│
└─ 키워드 텍스트 검색 (직접 포함 → 별칭 매칭 → 재료 캐시 매칭)
    ↓
경고 표시 (빨간 테두리 카드 + ⚠️ 인라인 배지)
```

### UI 표시 방식

| 페이지 | 부모 로그인 시 알레르기 표시 |
|--------|--------------------------|
| 식단표 (page.note.meal) | 해당 끼니 카드 **빨간 테두리**(`#e74c3c`) + **연한 빨간 배경**(`#fff5f5`) + `⚠️ 알레르기 주의: ...` 텍스트 |
| 오늘의 식단 (page.note.today) | 동일: **빨간 테두리** + **연한 빨간 배경** + `⚠️ ...` 인라인 경고 |

---

## 설치 및 환경 설정

### 사전 요구사항

| 항목 | 버전 | 비고 |
|------|------|------|
| WIZ Framework | 최신 | https://github.com/aspect-apps/wiz |
| Python | 3.10+ | WIZ 프레임워크 런타임 |
| Node.js | 18+ | Angular 빌드 |
| MySQL | 8.0+ | `utf8mb4` 캐릭터셋 |
| Google Gemini API Key | — | [AI Studio](https://aistudio.google.com/app/apikey)에서 발급 |
| 식약처 API Key | — | [공공데이터포털](https://www.data.go.kr/)에서 `식품영양성분DB` 활용 신청 |

### 1. WIZ 프레임워크 설치

```bash
# WIZ 프레임워크 설치 (공식 문서 참조)
pip install season-wiz

# 프로젝트 디렉토리로 이동
cd /opt/app
```

### 2. 데이터베이스 생성

MySQL에 접속하여 2개의 데이터베이스를 생성합니다:

```sql
CREATE DATABASE login_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE childcheck CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

테이블은 WIZ 서비스 최초 실행 시 Peewee ORM의 `create_table()`이 자동으로 생성합니다.

### 3. 설정 파일 생성

`config/` 디렉토리는 `.gitignore`에 포함되어 있으므로 직접 생성해야 합니다.

#### config/database.py

```python
from season import stdClass

login_db = stdClass(
    type="mysql",
    database="login_db",
    host="127.0.0.1",          # MySQL 호스트
    port=3306,                  # MySQL 포트
    user="root",                # MySQL 사용자
    password="YOUR_DB_PASSWORD", # MySQL 비밀번호
    charset='utf8mb4',
    init_command="SET time_zone='+09:00'"
)

childcheck = stdClass(
    type="mysql",
    database="childcheck",
    host="127.0.0.1",
    port=3306,
    user="root",
    password="YOUR_DB_PASSWORD",
    charset='utf8mb4',
    init_command="SET time_zone='+09:00'"
)
```

#### config/season.py

```python
# SMTP 설정 (Gmail 앱 비밀번호 사용)
smtp_host = "smtp.gmail.com"
smtp_port = 587
smtp_sender = "your-email@gmail.com"       # 발신 이메일
smtp_password = "YOUR_GMAIL_APP_PASSWORD"   # Gmail 앱 비밀번호 (16자리)

# Gemini AI 설정
class gemini:
    api_key = "YOUR_GEMINI_API_KEY"         # Google AI Studio에서 발급
    model = "gemini-2.5-flash-lite"         # 사용할 모델

# Web Push (VAPID) 설정
class vapid:
    public_key = "YOUR_VAPID_PUBLIC_KEY"    # VAPID 공개키
    private_key = "YOUR_VAPID_PRIVATE_KEY"  # VAPID 비밀키
    claims_email = "your-email@gmail.com"
```

> **Gmail 앱 비밀번호 발급 방법**: Google 계정 → 보안 → 2단계 인증 활성화 → 앱 비밀번호 생성 (메일 선택)

> **VAPID 키 생성**: `npx web-push generate-vapid-keys` 명령으로 생성

### 4. 식품DB 초기 데이터 적재 (55만건)

`nutrition_foods` 테이블에 국가표준식품성분 데이터를 적재해야 영양 분석이 정상 동작합니다.

#### 데이터 소스

- **식품의약품안전처 식품영양성분 데이터베이스**: [공공데이터포털](https://www.data.go.kr/)에서 CSV 다운로드
- API 서비스키: `FOOD_SAFETY_API_KEY` 환경변수로 설정

#### 적재 방법

```bash
# 환경변수 설정
export FOOD_SAFETY_API_KEY="YOUR_FOOD_SAFETY_API_KEY"
```

적재 스크립트는 `nutrition_api.py`의 식약처 API 호출 로직을 활용하거나, CSV를 직접 MySQL에 import합니다:

```sql
-- CSV 직접 적재 예시
LOAD DATA LOCAL INFILE '/path/to/nutrition_data.csv'
INTO TABLE nutrition_foods
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;
```

> ⚠️ 식품DB 없이도 서비스는 동작하지만, 영양 분석이 `BASIC_INGREDIENTS` 사전과 식품군 표준값으로만 fallback되어 정확도가 낮아집니다.

### 5. 영양 가이드라인 데이터

`data/` 디렉토리도 `.gitignore`에 포함되어 있으므로 직접 생성합니다:

```bash
mkdir -p data
```

`data/nutrition_guideline.json` 파일을 아래 구조로 생성합니다:

```json
{
    "source": "식품의약품안전처 / 어린이급식관리지원센터 (2013.05)",
    "title": "영유아 단체급식 가이드라인 1인 1회 적정 배식량",
    "food_group_standards": {
        "곡류": {
            "calories": 190, "protein": 2.5, "fat": 0.3,
            "carbs": 44.0, "calcium": 3.0, "iron": 0.3,
            "serving": "밥 130g (2/3공기)"
        },
        "고기류": {
            "calories": 50, "protein": 5.0, "fat": 2.0,
            "carbs": 0.0, "calcium": 5.0, "iron": 0.5,
            "serving": "육류 30g (1/2접시)"
        },
        "채소류": {
            "calories": 7, "protein": 0.5, "fat": 0.1,
            "carbs": 1.0, "calcium": 15.0, "iron": 0.2,
            "serving": "채소 30g"
        },
        "국류": {
            "calories": 25, "protein": 1.0, "fat": 0.3,
            "carbs": 4.0, "calcium": 10.0, "iron": 0.2,
            "serving": "국 140ml"
        },
        "김치류": {
            "calories": 3, "protein": 0.2, "fat": 0.05,
            "carbs": 0.5, "calcium": 5.0, "iron": 0.1,
            "serving": "김치 20g"
        },
        "과일류": {
            "calories": 25, "protein": 0.3, "fat": 0.1,
            "carbs": 6.0, "calcium": 5.0, "iron": 0.1,
            "serving": "과일 80g"
        },
        "유제품": {
            "calories": 120, "protein": 6.0, "fat": 6.0,
            "carbs": 9.0, "calcium": 200.0, "iron": 0.1,
            "serving": "우유 200ml"
        }
    },
    "daily_targets": {
        "1-2": {
            "calories": 420, "protein": 20, "fat": 17,
            "carbs": 73, "calcium": 250, "iron": 3.3
        },
        "3-5": {
            "calories": 640, "protein": 12.5, "fat": 23,
            "carbs": 102, "calcium": 275, "iron": 4.5
        }
    },
    "serving_counts": {
        "1-2": {
            "lunch": {"곡류": 0.7, "고기류": 1.5, "채소류": 1.5, "국류": 1.0, "김치류": 1.0},
            "snack": {"곡류": 0.3, "과일류": 1.0, "유제품": 1.0}
        },
        "3-5": {
            "lunch": {"곡류": 1.0, "고기류": 2.0, "채소류": 2.5, "국류": 1.0, "김치류": 1.0},
            "snack": {"곡류": 0.5, "과일류": 1.5, "유제품": 1.0}
        }
    }
}
```

### 6. Python 의존성 설치

```bash
# 프로젝트 디렉토리에서 실행
pip install peewee pymysql bcrypt pyhwpx pywebpush google-genai requests
```

| 패키지 | 용도 |
|--------|------|
| `peewee` | ORM (MySQL 연동) |
| `pymysql` | MySQL 드라이버 |
| `bcrypt` | 비밀번호 해싱 |
| `pyhwpx` | HWP 파일 파싱 (식단표 업로드) |
| `pywebpush` | Web Push 알림 |
| `google-genai` | Google Gemini AI API |
| `requests` | HTTP 클라이언트 (식약처 API) |

---

## 빌드 및 실행

### 프로젝트 빌드

```bash
# 일반 빌드 (기존 코드 수정 시)
cd /opt/app && wiz project build --project=main

# 클린 빌드 (새 API 함수 추가/삭제/이름 변경 시)
cd /opt/app && wiz project build --project=main --clean
```

### 서비스 실행

```bash
# WIZ 서비스 시작
cd /opt/app && wiz run
```

기본 포트는 `3000`이며, `http://localhost:3000`으로 접속합니다.

### 초기 사용 흐름

1. **원장 계정 생성**: 회원가입 페이지에서 "원장" 역할로 가입
2. **서버(어린이집) 생성**: 로그인 후 서버 생성 (서버 코드 자동 발급)
3. **교사/학부모 참여**: 서버 코드를 입력하여 참여
4. **식단 등록**: 교사/원장이 HWP 파일 업로드 또는 수동 등록
5. **기능 사용**: 오늘의 식단, 영양 분석, AI 저녁 추천 등

---

## 역할별 기능 매트릭스

| 기능 | 학부모 | 교사 | 원장 |
|------|--------|------|------|
| 오늘의 식단 확인 | ✅ | ✅ | ✅ |
| AI 저녁 추천 | ✅ | — | — |
| 알레르기 경고 | ✅ (자녀) | ✅ (전체) | ✅ (전체) |
| 식단 등록/수정 | — | ✅ | ✅ |
| HWP 식단 업로드 | — | ✅ | ✅ |
| 대체식 선택 | — | ✅ | ✅ |
| 활동 기록 작성 | — | ✅ | — |
| 알림장 승인 | — | — | ✅ |
| 건강 체크 | ✅ | — | — |
| 프로필 사진 | ✅ | — | — |
| 서버 생성 | — | — | ✅ |
| 반(클래스) 관리 | — | — | ✅ |
| 프로필 목록 | — | ✅ (담당) | ✅ (전체) |
| 월간 영양 대시보드 | — | ✅ | ✅ |
| 알레르기 관리/통계 | — | — | ✅ |

---

## 라이선스

이 프로젝트는 개인 학습 목적으로 개발되었습니다.
