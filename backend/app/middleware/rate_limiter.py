"""
Rate Limiting 미들웨어 모듈.
slowapi를 사용해 IP당 분당 요청 수를 제한하고,
한도 초과 시 Slack 알림을 발송합니다.
"""

import logging

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import get_settings
from app.services.billing_monitor import send_slack_alert

logger = logging.getLogger(__name__)
settings = get_settings()

# slowapi 전역 Limiter 인스턴스 (싱글톤)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
)


async def rate_limit_exceeded_handler(request: Request, exc: Exception) -> None:
    """
    Rate limit 초과 시 호출되는 핸들러.
    차단된 IP 정보를 로깅하고 Slack 알림을 발송합니다.

    Args:
        request: FastAPI Request 객체
        exc: slowapi RateLimitExceeded 예외
    """
    client_ip = get_remote_address(request)
    path = request.url.path
    logger.warning(
        "Rate limit exceeded: ip=%s, path=%s, limit=%d/min",
        client_ip, path, settings.RATE_LIMIT_PER_MINUTE,
    )
    message = (
        f":no_entry: *AudioScope Abuse 감지*\n"
        f"• IP: `{client_ip}`\n"
        f"• 경로: `{path}`\n"
        f"• 제한: {settings.RATE_LIMIT_PER_MINUTE}req/min 초과"
    )
    # 비동기 알림 (실패해도 요청 처리에 영향 없음)
    try:
        import asyncio
        asyncio.create_task(send_slack_alert(message))
    except RuntimeError:
        # 이벤트 루프가 없는 컨텍스트에서는 무시
        logger.debug("Could not create task for Slack alert outside event loop.")
