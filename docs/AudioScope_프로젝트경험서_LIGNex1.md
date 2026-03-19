# AudioScope - AI 뉴스 오디오 브리핑 서비스

> **프로젝트 유형**: 1인 풀스택 개발 (기획 → 설계 → 구현 → 배포)
> **개발 기간**: 2025.01 ~ 현재 (운영 중)
> **규모**: Backend 3,500+ LOC (Python) / Frontend 4,400+ LOC (Dart) / 총 7,900+ LOC

---

## 1. 프로젝트 개요

바쁜 직장인을 위한 **AI 기반 뉴스 오디오 브리핑 앱**입니다.
매일 3회(06시/12시/18시) 자동으로 뉴스를 수집하고, AI가 요약한 스크립트를 TTS 음성으로 변환하여 제공합니다.

**핵심 가치**: 뉴스를 읽을 시간이 없는 사용자에게, 출퇴근길이나 점심시간에 귀로 듣는 맞춤형 뉴스 경험 제공

---

## 2. 기술 스택

| 영역 | 기술 |
|------|------|
| **Backend** | Python 3.12, FastAPI, SQLAlchemy 2.0 (async), PostgreSQL, Redis, APScheduler |
| **Frontend** | Flutter 3, Dart, Riverpod (상태관리), GoRouter (내비게이션), just_audio |
| **AI/ML Pipeline** | Naver News API → Google Gemini 2.5 Flash (요약) → Supertone Play (TTS) |
| **인증** | Firebase Auth (Google/Apple/Kakao OAuth) + JWT (HS256) |
| **스토리지** | Supabase Storage (S3 호환), CDN 배포 |
| **인프라** | Docker, Render (Backend), GitHub Actions CI/CD |
| **모니터링** | Slack Webhook 알림, 구조화 로깅, 비용 추적 시스템 |

---

## 3. 시스템 아키텍처

```
[사용자 앱 (Flutter)]
        │
        ▼
[FastAPI Backend] ──── [PostgreSQL] (9개 테이블)
        │
        ├── [Firebase Auth] ← Google/Apple/Kakao OAuth
        │
        ├── [APScheduler] ──── 매일 3회 자동 실행
        │       │
        │       ├── [Naver News API] → 뉴스 수집 (카테고리별)
        │       ├── [Gemini 2.5 Flash] → AI 스크립트 생성
        │       ├── [Supertone TTS] → 음성 합성
        │       └── [Supabase Storage] → 오디오 파일 저장
        │
        ├── [Redis] ──── Rate Limiting, 세션 캐시
        └── [Slack] ──── 비용 초과/장애 알림
```

---

## 4. 핵심 구현 내용

### 4-1. 자동화된 뉴스 처리 파이프라인

**문제**: 하루 3회, 10개 카테고리의 뉴스를 수집하고 요약하여 음성으로 변환하는 전체 과정을 무인 자동화해야 함

**해결**:
- APScheduler 기반 **크론 스케줄링** (06:00/12:00/18:00 KST)
- 파이프라인 단계: 뉴스 수집 → 중복 제거 → AI 요약 → TTS 변환 → 스토리지 업로드 → DB 저장
- 각 단계별 **에러 격리**: 한 단계 실패 시 fallback 스크립트로 대체하여 서비스 중단 방지
- **비용 모니터링**: Gemini 일일 $1, Supertone 월 $30 한도 설정 및 Slack 알림

**기술적 성과**:
- 비동기(async/await) 처리로 파이프라인 전체 실행 시간 최적화
- 토큰 단위 비용 추적 (Input: $0.075/1M tokens, Output: $0.3/1M tokens)

### 4-2. 비동기 데이터베이스 설계 (ACID 보장)

**문제**: 동시 사용자 요청과 백그라운드 스케줄러가 DB에 동시 접근하는 환경에서 데이터 정합성 보장

**해결**:
- SQLAlchemy 2.0 **async engine** + Connection Pooling (pool_size=5, max_overflow=10)
- FastAPI 의존성 주입 패턴으로 **자동 커밋/롤백** 처리
- 스케줄러용 별도 **Context Manager** 세션 분리
- `pool_pre_ping=True`로 끊어진 연결 자동 복구

**DB 스키마** (9개 테이블):
| 테이블 | 역할 |
|--------|------|
| users | 사용자 프로필, Firebase UID, FCM 토큰 |
| user_category_preferences | 뉴스 카테고리 개인화 설정 |
| briefings | 브리핑 메타데이터 (기간, 스크립트, 오디오 URL) |
| briefing_articles | 브리핑 내 개별 뉴스 기사 |
| subscriptions | 프리미엄 구독 관리 (플랜, 상태, 만료일) |
| listen_histories | 청취 이력 추적 (진행률, 완료 여부) |
| billing_usages | API 비용 추적 (서비스별, 일별) |
| referrals | 추천인 보상 시스템 |
| word_trends | 키워드 트렌드 분석 결과 |

### 4-3. RESTful API 설계 (27개 엔드포인트)

**6개 라우터로 도메인별 분리**:

| 라우터 | 엔드포인트 수 | 주요 기능 |
|--------|:---:|------|
| **Briefings** | 8 | 오늘의 브리핑, 히스토리, 미청취 목록, 청취 기록 |
| **Users** | 8 | Firebase→JWT 인증, 프로필 CRUD, 카테고리 관리, 음성 선택 |
| **Subscriptions** | 5 | 구독 상태, 업그레이드, 취소, 광고 보상, 접근 권한 확인 |
| **Referrals** | 2 | 추천 코드 발급, 코드 적용 |
| **Trends** | 1 | 주간 키워드 트렌드 |
| **Admin** | 4 | 수동 브리핑 생성, 비용 현황, 시스템 통계, 상세 헬스체크 |

### 4-4. 인증 및 보안 체계

- **다중 OAuth**: Google, Apple, Kakao 3개 소셜 로그인 지원
- **이중 토큰 구조**: Firebase ID Token(클라이언트) → 서버 검증 → JWT Access Token 발급
- **보안 계층**:
  - IP 기반 Rate Limiting (60 req/min, Redis 또는 인메모리)
  - Request ID 미들웨어로 요청 추적
  - JWT 만료 시간 관리 (Access: 60분, Refresh: 30일)
  - 프로덕션 환경 JWT Secret 기본값 사용 차단 (Validator)

### 4-5. 프리미엄 구독 & 수익화 모델

**비즈니스 로직**:
- **무료 사용자**: 아침 브리핑만 제공 + 광고 보상으로 1일 1회 추가 청취
- **프리미엄**: 월 ₩4,900 / 연 ₩39,000 (전체 브리핑 접근)
- **추천 보상**: 3명 추천 시 7일 프리미엄 무료 체험
- **구독 만료 자동 처리**: 매일 00:05 KST 스케줄러로 만료 체크

### 4-6. Flutter 모바일 앱 (13개 화면)

| 화면 | 핵심 구현 |
|------|----------|
| **Splash/Onboarding** | Firebase 초기화, 인증 상태 분기, 캐러셀 튜토리얼 |
| **Login** | 3개 소셜 로그인 버튼, 로딩 상태 관리 |
| **Home** | Bottom Navigation (브리핑/트렌드/설정), 탭 상태 유지 |
| **Briefing** | 일별 브리핑 목록, 프리미엄 잠금 표시, 풀다운 새로고침 |
| **Audio Player** | just_audio 기반 재생/일시정지/진행바, 백그라운드 재생 |
| **Category** | 다중 선택 UI, 우선순위 정렬, 서버 동기화 |
| **Subscription** | 플랜 비교 카드, 결제 CTA, 상태별 UI 분기 |
| **Trends** | 주간 키워드 순위, 빈도 시각화 |
| **Settings** | 프로필/음성/카테고리/법적 고지 통합 관리 |

**주요 아키텍처 패턴**:
- **Riverpod**: 전역 상태 관리 (인증, 사용자 데이터, 브리핑 캐시)
- **GoRouter**: 선언적 라우팅 + 인증 가드
- **Dio Interceptor**: JWT 자동 첨부 + 401 처리 → 로그아웃 콜백
- **FlutterSecureStorage**: 토큰 암호화 저장

### 4-7. 한국어 NLP 키워드 트렌드

- KoNLPy(Okt) 형태소 분석기로 **명사 추출**
- 한국어 불용어 필터링 (조사, 일반 명사 제거)
- 주간 상위 50개 키워드 저장 및 카테고리 태깅
- 라이브러리 미설치 환경 대비 **정규식 기반 fallback** 구현

---

## 5. 문제 해결 사례

### Case 1: Firebase 인증 서버리스 환경 적용

**문제**: Render 배포 환경에서 Firebase credentials JSON 파일을 직접 배치할 수 없음
**해결**: Base64 인코딩된 JSON을 환경변수로 주입 → 런타임에 디코딩하여 Firebase Admin SDK 초기화
**결과**: CI/CD 파이프라인에서 시크릿 관리와 배포 자동화 양립

### Case 2: TTS 비용 최적화

**문제**: Supertone TTS API 호출 비용이 텍스트 길이에 비례하여 증가
**해결**:
- 스크립트 길이 제한 (500~1,200자)
- 월간 $30 비용 한도 설정 + 임계치 도달 시 Slack 알림
- 한도 초과 시 fallback 스크립트 사용으로 서비스 연속성 보장

### Case 3: 동시성 환경에서의 청취 이력 정합성

**문제**: 같은 사용자가 여러 기기에서 동시 청취 시 listen_history 중복 발생
**해결**: (user_id, briefing_id) UNIQUE 제약조건 + Upsert 로직으로 delta만 업데이트

---

## 6. 프로젝트를 통해 습득한 역량

| 역량 | 상세 |
|------|------|
| **풀스택 설계** | 기획부터 배포까지 1인 전체 사이클 수행 경험 |
| **비동기 프로그래밍** | Python asyncio, SQLAlchemy async, httpx 기반 I/O 최적화 |
| **API 설계** | RESTful 원칙 준수, 27개 엔드포인트 도메인 분리 설계 |
| **DB 설계** | 9개 테이블 정규화, Connection Pooling, 트랜잭션 관리 |
| **외부 API 통합** | 5개 외부 서비스 연동 (Naver, Gemini, Supertone, Firebase, Supabase) |
| **CI/CD** | GitHub Actions → Render 자동 배포 파이프라인 구축 |
| **보안** | OAuth 2.0 다중 인증, JWT 토큰 관리, Rate Limiting |
| **비용 관리** | API 사용량 실시간 추적 및 한도 기반 자동 알림 체계 |
| **모바일 개발** | Flutter 크로스플랫폼 앱, Material 3 디자인 시스템 |

---

## 7. 향후 계획

- Google Play Store 정식 출시
- iOS 빌드 및 App Store 배포
- FCM 기반 브리핑 도착 푸시 알림
- 사용자 피드백 기반 AI 요약 품질 개선
- A/B 테스트를 통한 프리미엄 전환율 최적화
