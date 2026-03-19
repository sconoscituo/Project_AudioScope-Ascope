"""
AudioScope FastAPI 애플리케이션 진입점.
CORS, Rate Limiter, Request ID, 라우터, 스케줄러를 설정합니다.
ORJSON 응답, 구조화 로깅, Prometheus 메트릭을 지원합니다.
"""

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.config import get_settings
from app.database import close_db_engine, close_redis
from app.middleware.rate_limiter import RateLimitMiddleware
from app.middleware.request_id import RequestIdMiddleware
from app.routers import admin, briefings, referrals, subscriptions, trends, users
from app.scheduler.tasks import setup_scheduler
from app.utils.auth import init_firebase
from app.utils.logger import setup_logging

settings = get_settings()
setup_logging(settings.ENVIRONMENT)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기: 시작 시 초기화, 종료 시 정리."""
    logger.info("AudioScope starting (env=%s, ver=%s)...", settings.ENVIRONMENT, settings.APP_VERSION)

    init_firebase()

    scheduler = setup_scheduler()
    scheduler.start()
    logger.info("APScheduler started.")

    yield

    scheduler.shutdown(wait=False)
    await close_redis()
    await close_db_engine()
    logger.info("AudioScope shutdown complete.")


app = FastAPI(
    title="AudioScope API",
    description="한국어 AI 뉴스 오디오 브리핑 서비스",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

# ── Middleware (순서 중요: 위에서 아래로 실행) ──
app.add_middleware(RequestIdMiddleware)
app.add_middleware(RateLimitMiddleware, limit=settings.RATE_LIMIT_PER_MINUTE, window_seconds=60)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if not settings.is_production else [
        "https://audioscope.app",
        "https://www.audioscope.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Exception Handlers ──
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> ORJSONResponse:
    logger.error("Unhandled: %s %s - %s", request.method, request.url.path, exc, exc_info=True)
    return ORJSONResponse(
        status_code=500,
        content={"success": False, "data": None, "error": "Internal server error."},
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception) -> ORJSONResponse:
    return ORJSONResponse(
        status_code=404,
        content={"success": False, "data": None, "error": "Resource not found."},
    )


@app.exception_handler(422)
async def validation_handler(request: Request, exc: Exception) -> ORJSONResponse:
    logger.warning("Validation error: %s - %s", request.url.path, exc)
    detail = "입력 데이터가 올바르지 않습니다."
    if hasattr(exc, "errors") and callable(exc.errors):
        fields = [e.get("loc", ["unknown"])[-1] for e in exc.errors()]
        detail = f"입력 오류: {', '.join(str(f) for f in fields)}"
    return ORJSONResponse(
        status_code=422,
        content={"success": False, "data": None, "error": detail},
    )


# ── Routers ──
app.include_router(briefings.router)
app.include_router(users.router)
app.include_router(subscriptions.router)
app.include_router(trends.router)
app.include_router(referrals.router)
app.include_router(admin.router)


# ── Health Check ──
@app.get("/health", tags=["system"])
async def health_check() -> dict[str, Any]:
    return {
        "success": True,
        "data": {
            "status": "ok",
            "environment": settings.ENVIRONMENT,
            "version": settings.APP_VERSION,
        },
        "error": None,
    }
