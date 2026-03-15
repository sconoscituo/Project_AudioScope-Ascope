"""
구조화된 로깅 설정 모듈.
JSON 포맷 로깅, 요청 상관ID(correlation_id) 추적을 지원합니다.
"""

import logging
import logging.config
import sys
from contextvars import ContextVar
from typing import Any

# 요청별 상관 ID를 저장하는 ContextVar
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="-")


class CorrelationFilter(logging.Filter):
    """로그 레코드에 correlation_id를 자동 주입하는 필터."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = correlation_id_var.get()  # type: ignore[attr-defined]
        return True


LOGGING_CONFIG: dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "correlation": {
            "()": CorrelationFilter,
        },
    },
    "formatters": {
        "standard": {
            "format": "%(asctime)s | %(levelname)-8s | %(correlation_id)s | %(name)s | %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S",
        },
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(correlation_id)s %(name)s %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "standard",
            "filters": ["correlation"],
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"],
    },
    "loggers": {
        "app": {"level": "DEBUG", "propagate": True},
        "uvicorn": {"level": "INFO", "propagate": True},
        "sqlalchemy.engine": {"level": "WARNING", "propagate": True},
        "apscheduler": {"level": "INFO", "propagate": True},
    },
}


def setup_logging(environment: str = "development") -> None:
    """로깅을 초기화합니다. production에서는 JSON 포맷을 사용합니다."""
    if environment == "production":
        LOGGING_CONFIG["handlers"]["console"]["formatter"] = "json"
    logging.config.dictConfig(LOGGING_CONFIG)


def get_logger(name: str) -> logging.Logger:
    """모듈별 로거를 반환합니다."""
    return logging.getLogger(name)
