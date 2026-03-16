"""
AudioScope 애플리케이션 설정 모듈.
pydantic-settings를 사용하여 환경변수를 로드하고 검증합니다.
"""

import logging
import os
from functools import lru_cache

from pydantic import FieldValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """애플리케이션 전체 설정 클래스."""

    model_config = SettingsConfigDict(
        env_file=f".env.{os.getenv('ENVIRONMENT', 'development')}",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Database ──
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/audioscope_dev"

    # ── Redis (선택사항 — 없으면 메모리 기반 Rate Limit 사용) ──
    REDIS_URL: str = ""

    # ── Firebase ──
    FIREBASE_CREDENTIALS_PATH: str = "./firebase-credentials.json"

    # ── AI / TTS ──
    GEMINI_API_KEY: str = ""
    SUPERTONE_API_KEY: str = ""

    # ── Naver News API ──
    NAVER_CLIENT_ID: str = ""
    NAVER_CLIENT_SECRET: str = ""

    # ── Supabase ──
    SUPABASE_URL: str = ""           # e.g. https://xxxx.supabase.co
    SUPABASE_SERVICE_KEY: str = ""   # service_role key
    SUPABASE_STORAGE_BUCKET: str = "audioscope-audio"

    # ── App ──
    ENVIRONMENT: str = "development"

    # ── JWT ──
    JWT_SECRET_KEY: str = "change-this-in-production-minimum-32-chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_EXPIRE_DAYS: int = 30

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret(cls, v: str, info: FieldValidationInfo) -> str:
        env = (info.data or {}).get("ENVIRONMENT", "development")
        if env == "production" and v == "change-this-in-production-minimum-32-chars":
            raise ValueError(
                "JWT_SECRET_KEY must be changed from the default value in production."
            )
        return v

    APP_VERSION: str = "1.0.0"

    # ── Billing limits ──
    GEMINI_DAILY_LIMIT_USD: float = 1.0
    SUPERTONE_MONTHLY_LIMIT_USD: float = 30.0

    # ── Rate limiting ──
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 10

    # ── Slack alerting ──
    SLACK_WEBHOOK_URL: str = ""

    # ── Freemium ──
    FREE_BRIEFING_PERIOD: str = "morning"
    PREMIUM_PRICE_KRW_MONTHLY: int = 4900
    PREMIUM_PRICE_KRW_YEARLY: int = 39000
    TRIAL_DAYS: int = 7

    # ── Briefing ──
    MAX_ARTICLES_PER_BRIEFING: int = 12
    BRIEFING_SCRIPT_MIN_CHARS: int = 500
    BRIEFING_SCRIPT_MAX_CHARS: int = 1200

    # ── News Categories (기본값) ──
    DEFAULT_CATEGORIES: str = "politics,economy,society,world,tech,science"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def default_category_list(self) -> list[str]:
        return [c.strip() for c in self.DEFAULT_CATEGORIES.split(",")]


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    logger.info("Settings loaded for environment: %s", settings.ENVIRONMENT)
    return settings
