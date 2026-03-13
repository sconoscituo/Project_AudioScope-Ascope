"""
AudioScope FastAPI 애플리케이션 진입점.
CORS, Rate Limiter, 글로벌 에러 핸들러, 라우터, 스케줄러를 설정합니다.
"""

import logging
import logging.config
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import get_settings
from app.middleware.rate_limiter import limiter
from app.routers import admin, briefings, users
from app.scheduler.tasks import setup_scheduler
from app.utils.auth import init_firebase

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 생명주기 관리.
    시작 시 Firebase 초기화, 스케줄러 시작.
    종료 시 스케줄러 정지.
    """
    logger.info("AudioScope starting up (env=%s)...", settings.ENVIRONMENT)

    # Firebase 초기화
    init_firebase()

    # 스케줄러 시작
    scheduler = setup_scheduler()
    scheduler.start()
    logger.info("APScheduler started.")

    yield

    # 종료
    scheduler.shutdown(wait=False)
    logger.info("APScheduler stopped. AudioScope shutting down.")


app = FastAPI(
    title="AudioScope API",
    description="한국어 AI 뉴스 오디오 브리핑 서비스 API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

# Rate Limiter 설정
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS 설정
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


# 글로벌 에러 핸들러
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    모든 미처리 예외를 잡아 통일된 에러 응답을 반환합니다.

    Args:
        request: FastAPI Request 객체
        exc: 발생한 예외

    Returns:
        JSONResponse: 에러 응답 (500)
    """
    logger.error(
        "Unhandled exception: method=%s, path=%s, error=%s",
        request.method, request.url.path, exc, exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"success": False, "data": None, "error": "Internal server error."},
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    """404 Not Found 응답을 통일된 포맷으로 반환합니다."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"success": False, "data": None, "error": "Resource not found."},
    )


@app.exception_handler(422)
async def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """422 Validation Error 응답을 통일된 포맷으로 반환합니다."""
    logger.warning("Validation error: path=%s, error=%s", request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"success": False, "data": None, "error": str(exc)},
    )


# 라우터 등록
app.include_router(briefings.router)
app.include_router(users.router)
app.include_router(admin.router)


@app.get("/health", tags=["system"])
async def health_check() -> dict[str, Any]:
    """
    기본 헬스체크 엔드포인트.

    Returns:
        dict: 서비스 상태 및 환경 정보
    """
    return {
        "success": True,
        "data": {"status": "ok", "environment": settings.ENVIRONMENT},
        "error": None,
    }
