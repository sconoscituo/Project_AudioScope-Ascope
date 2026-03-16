"""
Rate Limiting 미들웨어 모듈.
간단한 in-memory 슬라이딩 윈도우 방식으로 IP당 분당 요청 수를 제한합니다.
외부 저장소(Redis) 없이도 동작하며, Redis가 있으면 활용합니다.
"""

import logging
import time
from collections import defaultdict, deque

from fastapi import Request, status
from fastapi.responses import ORJSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings
from app.services.billing_monitor import send_slack_alert

logger = logging.getLogger(__name__)
settings = get_settings()

# ── In-memory sliding window store ──
# { ip: deque of timestamps }
_request_log: dict[str, deque] = defaultdict(deque)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """슬라이딩 윈도우 In-memory Rate Limiter."""

    def __init__(self, app, limit: int = 60, window_seconds: int = 60) -> None:
        super().__init__(app)
        self.limit = limit
        self.window = window_seconds

    async def dispatch(self, request: Request, call_next):
        # Health check는 rate limit 면제
        if request.url.path == "/health":
            return await call_next(request)

        ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        window_start = now - self.window

        dq = _request_log[ip]
        # 오래된 항목 제거
        while dq and dq[0] < window_start:
            dq.popleft()

        if len(dq) >= self.limit:
            logger.warning("Rate limit exceeded: ip=%s, path=%s", ip, request.url.path)
            try:
                import asyncio
                asyncio.create_task(send_slack_alert(
                    f":no_entry: *AudioScope 어뷰징 감지*\n"
                    f"- IP: `{ip}`\n"
                    f"- 경로: `{request.url.path}`\n"
                    f"- 제한: {self.limit}req/{self.window}s 초과"
                ))
            except RuntimeError:
                pass
            return ORJSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"success": False, "data": None, "error": "Too many requests. Please slow down."},
                headers={"Retry-After": str(self.window)},
            )

        dq.append(now)
        return await call_next(request)
