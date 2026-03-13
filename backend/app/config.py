"""
AudioScope 애플리케이션 설정 모듈.
pydantic-settings를 사용하여 환경변수를 로드하고 검증합니다.
"""

import logging
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """애플리케이션 전체 설정 클래스."""

    model_config = SettingsConfigDict(
        env_file=".env.development",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    DATABASE_URL: str

    # Firebase
    FIREBASE_CREDENTIALS_PATH: str = "./firebase-credentials.json"

    # AI / TTS
    GEMINI_API_KEY: str
    SUPERTONE_API_KEY: str

    # Naver News API
    NAVER_CLIENT_ID: str
    NAVER_CLIENT_SECRET: str

    # Cloudflare R2
    R2_ACCOUNT_ID: str
    R2_ACCESS_KEY_ID: str
    R2_SECRET_ACCESS_KEY: str
    R2_BUCKET_NAME: str
    R2_PUBLIC_URL: str

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    # App
    ENVIRONMENT: str = "development"

    # Billing limits
    GEMINI_DAILY_LIMIT_USD: float = 1.0
    SUPERTONE_MONTHLY_LIMIT_USD: float = 30.0

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 50

    # Slack alerting
    SLACK_WEBHOOK_URL: str = ""

    @property
    def is_production(self) -> bool:
        """운영 환경 여부를 반환합니다."""
        return self.ENVIRONMENT == "production"


@lru_cache()
def get_settings() -> Settings:
    """
    설정 싱글톤을 반환합니다.

    Returns:
        Settings: 애플리케이션 설정 인스턴스
    """
    settings = Settings()
    logger.info("Settings loaded for environment: %s", settings.ENVIRONMENT)
    return settings
