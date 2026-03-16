"""
SQLAlchemy async 데이터베이스 + Redis 설정 모듈.
비동기 엔진, 세션 팩토리, Base 클래스, Redis 연결을 제공합니다.
ACID 원칙 준수: 트랜잭션 격리, 낙관적 잠금, 자동 롤백.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import AsyncAdaptedQueuePool

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Async Engine (Connection Pooling 최적화) ──
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    poolclass=AsyncAdaptedQueuePool,
)

# ── Session Factory ──
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """모든 SQLAlchemy 모델의 기반 클래스."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI 의존성 주입용 DB 세션 생성기.
    ACID 보장: 자동 커밋/롤백 처리.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            logger.error("DB session rollback triggered", exc_info=True)
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    스케줄러 등 비-FastAPI 컨텍스트용 DB 세션 컨텍스트 매니저.
    with 문으로 사용하며 ACID를 보장합니다.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            logger.error("DB context session rollback triggered", exc_info=True)
            raise
        finally:
            await session.close()


# ── Redis 연결 ──
_redis_pool: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Redis 싱글톤 연결을 반환합니다."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=50,
        )
    return _redis_pool


async def close_redis() -> None:
    """Redis 연결을 종료합니다."""
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.close()
        _redis_pool = None


async def close_db_engine() -> None:
    """DB 엔진을 안전하게 종료합니다."""
    await engine.dispose()
