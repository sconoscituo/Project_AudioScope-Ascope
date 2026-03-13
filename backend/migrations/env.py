"""
Alembic 환경 설정 모듈.
비동기 SQLAlchemy 엔진을 지원하는 async 마이그레이션 설정입니다.
"""

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Alembic Config 객체
config = context.config

# 로깅 설정
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# .env에서 DATABASE_URL 오버라이드
from dotenv import load_dotenv
env = os.getenv("ENVIRONMENT", "development")
load_dotenv(f".env.{env}")
database_url = os.getenv("DATABASE_URL", "")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

# 모든 모델 메타데이터 임포트
from app.database import Base
import app.models.user       # noqa: F401
import app.models.briefing   # noqa: F401
import app.models.billing    # noqa: F401

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    오프라인 모드로 마이그레이션을 실행합니다.
    DB 연결 없이 SQL 스크립트를 생성합니다.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    실제 마이그레이션을 동기적으로 실행합니다.

    Args:
        connection: SQLAlchemy 동기 Connection 객체
    """
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """비동기 엔진으로 마이그레이션을 실행합니다."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """온라인 모드로 비동기 마이그레이션을 실행합니다."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
