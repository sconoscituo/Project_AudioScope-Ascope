# AudioScope

한국어 AI 뉴스 오디오 브리핑 앱.
바쁜 직장인을 위해 아침/점심/저녁(06:00/12:00/18:00 KST) 하루 3회 뉴스를 AI가 요약하고 TTS로 읽어주는 서비스입니다.

## 아키텍처

```
스케줄러(06:00/12:00/18:00 KST)
  → 네이버 뉴스 API로 기사 수집
  → Gemini 2.5 Flash로 한국어 스크립트 생성
  → Supertone Play TTS로 mp3 변환
  → Cloudflare R2에 업로드
  → 유저 요청 시 캐시된 URL 서빙 (API 비용 고정)
```

## 기술 스택

| 영역 | 기술 |
|------|------|
| Backend | Python 3.12 / FastAPI |
| ORM | SQLAlchemy 2.0 + Alembic |
| DB | PostgreSQL (Railway) |
| Storage | Cloudflare R2 |
| Auth | Firebase Auth (카카오/구글/애플) |
| TTS | Supertone Play API |
| AI 요약 | Gemini 2.5 Flash |
| 뉴스 | 네이버 검색 API + RSS |
| App | Flutter 3 |

## 프로젝트 구조

```
[AudioScope]/
├── backend/
│   ├── app/
│   │   ├── config.py          # 환경변수 설정 (pydantic-settings)
│   │   ├── database.py        # SQLAlchemy async 엔진
│   │   ├── main.py            # FastAPI 앱 진입점
│   │   ├── models/            # SQLAlchemy 모델
│   │   │   ├── user.py
│   │   │   ├── briefing.py
│   │   │   └── billing.py
│   │   ├── schemas/           # Pydantic 스키마
│   │   │   ├── briefing.py
│   │   │   └── user.py
│   │   ├── services/          # 비즈니스 로직
│   │   │   ├── news_fetcher.py    # 네이버 뉴스 수집
│   │   │   ├── summarizer.py      # Gemini AI 요약
│   │   │   ├── tts.py             # Supertone TTS
│   │   │   ├── storage.py         # Cloudflare R2
│   │   │   └── billing_monitor.py # 빌링 모니터링
│   │   ├── scheduler/
│   │   │   └── tasks.py       # APScheduler 작업
│   │   ├── middleware/
│   │   │   └── rate_limiter.py
│   │   ├── routers/
│   │   │   ├── briefings.py   # GET /api/v1/briefings/*
│   │   │   ├── users.py       # POST /api/v1/users/*
│   │   │   └── admin.py       # POST /api/v1/admin/*
│   │   └── utils/
│   │       └── auth.py        # Firebase/JWT 인증
│   ├── migrations/            # Alembic 마이그레이션
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── railway.toml
│   ├── .env.development       # 개발 환경변수 (gitignore됨)
│   └── .env.production        # 운영 환경변수 (gitignore됨)
└── flutter_app/
    ├── lib/
    │   ├── main.dart
    │   ├── core/
    │   │   ├── api/api_client.dart
    │   │   └── auth/auth_service.dart
    │   └── features/
    │       ├── briefing/
    │       │   ├── briefing_screen.dart
    │       │   └── audio_player_widget.dart
    │       └── auth/
    │           └── login_screen.dart
    └── pubspec.yaml
```

## 로컬 개발 환경 설정

### 사전 요구사항

- Python 3.12+
- PostgreSQL 15+
- Redis 7+
- Flutter 3.22+

### Backend 설정

```bash
cd backend

# 가상환경 생성 및 활성화
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp .env.development .env.development.local
# .env.development.local을 편집하여 실제 값 입력

# DB 마이그레이션
alembic upgrade head

# 서버 실행
uvicorn app.main:app --reload --port 8000
```

### Flutter 설정

```bash
cd flutter_app

# 의존성 설치
flutter pub get

# Firebase 설정
# google-services.json (Android) / GoogleService-Info.plist (iOS) 추가 필요

# 앱 실행
flutter run
```

## 환경변수 목록

| 변수명 | 설명 | 예시 |
|--------|------|------|
| `DATABASE_URL` | PostgreSQL 연결 URL | `postgresql+asyncpg://user:pw@host:5432/db` |
| `REDIS_URL` | Redis 연결 URL | `redis://localhost:6379` |
| `FIREBASE_CREDENTIALS_PATH` | Firebase 서비스 계정 키 경로 | `./firebase-credentials.json` |
| `GEMINI_API_KEY` | Google AI API 키 | `AIza...` |
| `SUPERTONE_API_KEY` | Supertone Play API 키 | `st_...` |
| `NAVER_CLIENT_ID` | 네이버 검색 API Client ID | `abc123` |
| `NAVER_CLIENT_SECRET` | 네이버 검색 API Client Secret | `xyz789` |
| `R2_ACCOUNT_ID` | Cloudflare 계정 ID | `abc123` |
| `R2_ACCESS_KEY_ID` | R2 액세스 키 ID | `...` |
| `R2_SECRET_ACCESS_KEY` | R2 시크릿 키 | `...` |
| `R2_BUCKET_NAME` | R2 버킷 이름 | `audioscope-dev` |
| `R2_PUBLIC_URL` | R2 공개 URL | `https://cdn.example.com` |
| `JWT_SECRET_KEY` | JWT 서명 비밀키 (32자 이상 랜덤) | `...` |
| `ENVIRONMENT` | 실행 환경 | `development` / `production` |
| `SLACK_WEBHOOK_URL` | Slack 알림 웹훅 URL | `https://hooks.slack.com/...` |
| `GEMINI_DAILY_LIMIT_USD` | Gemini 일일 비용 한도 | `1.0` |
| `SUPERTONE_MONTHLY_LIMIT_USD` | Supertone 월간 비용 한도 | `30.0` |
| `RATE_LIMIT_PER_MINUTE` | IP당 분당 최대 요청 수 | `50` |

## API 엔드포인트

### 인증 불필요
- `GET /health` - 기본 헬스체크

### 인증 필요 (JWT Bearer)
- `GET /api/v1/briefings/today` - 오늘의 브리핑 목록
- `GET /api/v1/briefings/{period}` - 특정 브리핑 상세
- `GET /api/v1/briefings/history` - 브리핑 히스토리
- `POST /api/v1/users/auth` - 로그인/회원가입
- `GET /api/v1/users/me` - 내 정보
- `DELETE /api/v1/users/me` - 회원탈퇴

### 관리자
- `POST /api/v1/admin/briefings/generate` - 수동 브리핑 생성
- `GET /api/v1/admin/billing` - 빌링 현황
- `GET /api/v1/admin/health` - 상세 헬스체크

## 응답 포맷

모든 API 응답은 통일된 포맷을 사용합니다:

```json
{
  "success": true,
  "data": {},
  "error": null
}
```

## 빌링 비용 추정

| 항목 | 비용 | 비고 |
|------|------|------|
| Gemini 2.5 Flash | ~$0.03/브리핑 | 기사 10건 요약 기준 |
| Supertone Play | ~$0.05/브리핑 | 4분 분량 기준 |
| **하루 3회 기준** | **~$0.24/일** | 유저 수 무관 고정비 |
| **월간** | **~$7.2/월** | R2 스토리지 별도 |

## Railway 배포

```bash
# Railway CLI 설치 후
cd backend
railway up
```

환경변수는 Railway 대시보드에서 직접 설정합니다.
