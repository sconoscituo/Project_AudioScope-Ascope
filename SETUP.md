# AudioScope - 프로젝트 설정 가이드

AI가 뉴스를 요약하고 TTS로 읽어주는 오디오 뉴스 브리핑 서비스입니다.
Flutter 앱(프론트엔드) + FastAPI 백엔드로 구성되어 있습니다.

---

## 1. 필요한 API 키 / 환경변수

| 환경변수 | 설명 | 발급 URL |
|---|---|---|
| `GEMINI_API_KEY` | 뉴스 요약 AI (Google Gemini) | https://aistudio.google.com/app/apikey |
| `SUPERTONE_API_KEY` | TTS 음성 합성 (Supertone) | https://supertone.ai |
| `NAVER_CLIENT_ID` | 네이버 뉴스 검색 API Client ID | https://developers.naver.com/apps |
| `NAVER_CLIENT_SECRET` | 네이버 뉴스 검색 API Secret | https://developers.naver.com/apps |
| `DATABASE_URL` | PostgreSQL 연결 URL | 직접 구성 (예: Railway, Supabase) |
| `REDIS_URL` | Redis 연결 URL (선택사항, 없으면 메모리 기반 Rate Limit 사용) | https://upstash.com |
| `FIREBASE_CREDENTIALS_JSON` | Firebase Admin SDK 인증 JSON (base64 인코딩) | https://console.firebase.google.com > 프로젝트 설정 > 서비스 계정 |
| `JWT_SECRET_KEY` | JWT 서명 비밀키 (최소 32자, 프로덕션에서 필수 변경) | 직접 생성 (`openssl rand -hex 32`) |
| `SUPABASE_URL` | Supabase 프로젝트 URL | https://supabase.com/dashboard |
| `SUPABASE_SERVICE_KEY` | Supabase service_role 키 | https://supabase.com/dashboard > 프로젝트 > API |
| `PORTONE_API_KEY` | 포트원 결제 API 키 | https://admin.portone.io |
| `PORTONE_API_SECRET` | 포트원 결제 API Secret | https://admin.portone.io |
| `SLACK_WEBHOOK_URL` | Slack 알림 Webhook URL (선택사항) | https://api.slack.com/apps |

---

## 2. GitHub Secrets 설정

GitHub 레포지토리 > **Settings > Secrets and variables > Actions > New repository secret** 에서 아래 항목을 추가합니다.

```
GEMINI_API_KEY
SUPERTONE_API_KEY
NAVER_CLIENT_ID
NAVER_CLIENT_SECRET
DATABASE_URL
REDIS_URL
FIREBASE_CREDENTIALS_JSON
JWT_SECRET_KEY
SUPABASE_URL
SUPABASE_SERVICE_KEY
PORTONE_API_KEY
PORTONE_API_SECRET
SLACK_WEBHOOK_URL
```

---

## 3. 로컬 개발 환경 설정

### 3-1. 백엔드 (.env 파일 생성)

```bash
cd backend
```

`.env.development` 파일을 생성합니다:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/audioscope_dev
REDIS_URL=redis://localhost:6379
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
GEMINI_API_KEY=your_gemini_api_key
SUPERTONE_API_KEY=your_supertone_api_key
NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET=your_naver_client_secret
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_KEY=your_supabase_service_key
JWT_SECRET_KEY=your-32-char-minimum-secret-key-here
ENVIRONMENT=development
PORTONE_API_KEY=your_portone_api_key
PORTONE_API_SECRET=your_portone_api_secret
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx
```

### 3-2. 백엔드 의존성 설치

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3-3. Flutter 앱 의존성 설치

```bash
cd flutter_app
flutter pub get
```

---

## 4. 실행 방법

### 백엔드 실행 (로컬)

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API 문서: http://localhost:8000/docs

### Flutter 앱 실행

```bash
cd flutter_app
flutter run
```

---

## 5. 배포 방법

### Docker Compose로 로컬 배포

```bash
cd backend
docker compose up --build
```

- API 서버: http://localhost:8000
- PostgreSQL: localhost:5432

### GitHub Actions 자동 배포

`.github/workflows/deploy.yml` 을 통해 `main` 브랜치에 push 시 자동 배포됩니다.
배포 전 위의 GitHub Secrets가 모두 설정되어 있어야 합니다.

### DB 마이그레이션 (Alembic)

```bash
cd backend
alembic upgrade head
```
