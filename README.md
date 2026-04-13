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
- [환경 설정](#환경-설정)
- [빌드 및 실행](#빌드-및-실행)

---

## 주요 기능

### 🍱 식단 관리

| 기능 | 설명 |
|------|------|
| 오늘의 식단 | 오전간식 / 점심 / 오후간식을 **타임라인 UI**로 확인 (학부모·교사 공통) |
| 연령별 메뉴 분기 | 1~2세 / 3~5세에 맞는 메뉴 자동 표시 (백김치↔배추김치 등) |
| 대체식 선택 | 교사/원장이 날짜별로 대체 메뉴를 선택하면 학부모에게 자동 반영 |
| 알레르기 경고 | 표준 19종 + 기타(커스텀) 알레르기 자동 감지 및 인라인 경고 |
| 식단표 업로드 | HWP 파일 파싱으로 월간 식단 일괄 등록 |
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
| 프론트엔드 | Angular 18 + Pug + Tailwind CSS + SCSS |
| 백엔드 | Python (WIZ exec 환경) |
| DB | MySQL (Peewee ORM) |
| AI | Google Gemini API |
| 영양 데이터 | 식약처 식품영양성분 DB API + 국가표준식품성분 로컬 DB (55만건) |
| 푸시 알림 | Web Push (Service Worker) |
| 이메일 | SMTP (Gmail) |
| 문서 파싱 | HWP 파일 파싱 (식단표 업로드) |

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
│   ├── page.myinfo/                      # 내 정보 관리
│   ├── page.pwa.install/                 # PWA 설치 안내
│   ├── layout.navbar/                    # 네비게이션 바 레이아웃
│   └── component.header/                 # 공통 헤더 컴포넌트
│
├── model/
│   ├── nutrition_api.py                  # 영양 검색 엔진 (6단계 파이프라인, 1175줄)
│   │   ├── analyze_meal_pipeline()       #   식단 → Gemini 정규화 → 병렬 검색 → 검증
│   │   ├── normalize_food_names()        #   Gemini로 식약처 검색용 이름 일괄 정규화
│   │   ├── search()                      #   단일 음식 6단계 검색│   │   ├── search_local()                #   로컬-only 검색 (API/AI 미호출, 결정적)│   │   ├── search_batch()                #   병렬 배치 검색
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
└── nutrition_guideline.json              # 식약처 가이드라인 기준 데이터 (식품군 표준값, 제공횟수 등)
```

---

## DB 스키마

### login_db (인증)

| 테이블 | 설명 | 주요 컬럼 |
|--------|------|-----------|
| users | 사용자 계정 | email, password, name, role |
| servers | 어린이집 서버 | name, code, owner_id |
| server_members | 서버-사용자 매핑 | server_id, user_id, role, class_name |

### childcheck (서비스)

| 테이블 | 설명 | 주요 컬럼 |
|--------|------|-----------|
| children | 자녀 정보 | user_id, name, birthdate, gender, profile_image |
| child_allergies | 자녀 알레르기 | child_id, allergy_type, other_detail |
| allergy_categories | 알레르기 카테고리 | category_name, allergy_numbers, caution_foods, substitute_foods |
| meals | 식단 데이터 | server_id, meal_date, meal_type, content, kcal, protein, kcal_35, protein_35, allergy_numbers, dish_allergies |
| meal_substitute_selections | 교사 대체식 선택 | meal_id, original_item, substitute_item, is_selected |
| meal_nutrition_cache | 영양분석 캐시 | server_id, meal_date, age_group, total_calories/protein/fat/carbs/calcium/iron, stage1_json |
| photos | 식단 사진 | server_id, meal_date, meal_type, photo_type, image_path |
| photo_comments | 사진 댓글 | photo_id, user_id, content |
| nutrition_foods | 식품성분 DB | food_name, calories, protein, ... (55만건) |
| nutrition_mapping | 영양소 매핑 캐시 | menu_name, nutrition_food_id, serving_ratio |
| notifications | 알림 | server_id, user_id, type, message |
| push_subscriptions | 푸시 구독 | user_id, endpoint, auth, p256dh |

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
경고 표시 (⚠️ 인라인 배지)
```

---

## 환경 설정

### 데이터베이스

config/database.py에서 설정:

| 네임스페이스 | 설명 |
|-------------|------|
| login_db | 인증 DB (users, servers, server_members) |
| childcheck | 서비스 DB (meals, children, 영양 등) |

### AI 설정

config/ai.py에서 설정:

```python
class gemini:
    api_key = "YOUR_GEMINI_API_KEY"
    model = "gemini-2.0-flash"
```

### 환경 변수

| 변수 | 설명 |
|------|------|
| DB_HOST | MySQL 호스트 (기본: 127.0.0.1) |
| DB_PORT | MySQL 포트 (기본: 3306) |
| DB_USER | MySQL 사용자 |
| DB_PASSWORD | MySQL 비밀번호 |
| FOOD_SAFETY_API_KEY | 식약처 식품영양성분 API 인증키 |
| SMTP_HOST | SMTP 서버 (기본: smtp.gmail.com) |
| SMTP_PORT | SMTP 포트 (기본: 587) |
| SMTP_SENDER | 발신 이메일 주소 |
| SMTP_PASSWORD | SMTP 앱 비밀번호 |

---

## 빌드 및 실행

```bash
# 프로젝트 빌드 (일반)
cd /opt/app && wiz project build --project=main

# 클린 빌드 (새 API 함수 추가/삭제 시)
cd /opt/app && wiz project build --project=main --clean
```

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
