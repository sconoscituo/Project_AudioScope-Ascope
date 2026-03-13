"""
SQLAlchemy async 데이터베이스 설정 모듈.
비동기 엔진, 세션 팩토리, Base 클래스를 제공합니다.
"""

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=not settings.is_production,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

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
    FastAPI 의존성 주입용 데이터베이스 세션 생성기.

    Yields:
        AsyncSession: 비동기 DB 세션
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
