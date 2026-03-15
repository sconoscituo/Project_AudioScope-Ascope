"""
Rate Limiting 미들웨어 모듈.
slowapi를 사용해 IP당 분당 요청 수를 제한합니다.
어뷰징 감지 시 Slack 알림을 발송합니다.
"""

import logging

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import get_settings
from app.services.billing_monitor import send_slack_alert

logger = logging.getLogger(__name__)
settings = get_settings()

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
    storage_uri=settings.REDIS_URL if settings.REDIS_URL else "memory://",
)


async def rate_limit_exceeded_handler(request: Request, exc: Exception) -> None:
    """Rate limit 초과 시 어뷰징 알림을 발송합니다."""
    client_ip = get_remote_address(request)
    path = request.url.path
    logger.warning("Rate limit exceeded: ip=%s, path=%s", client_ip, path)

    message = (
        f":no_entry: *AudioScope 어뷰징 감지*\n"
        f"- IP: `{client_ip}`\n"
        f"- 경로: `{path}`\n"
        f"- 제한: {settings.RATE_LIMIT_PER_MINUTE}req/min 초과"
    )
    try:
        import asyncio
        asyncio.create_task(send_slack_alert(message))
    except RuntimeError:
        pass
