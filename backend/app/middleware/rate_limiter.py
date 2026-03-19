"""
Rate Limiting 미들웨어 모듈.
슬라이딩 윈도우 방식으로 IP당 분당 요청 수를 제한합니다.
주기적으로 비활성 IP 항목을 정리하여 메모리 누수를 방지합니다.
"""

import asyncio
import logging
import time
import threading
from collections import deque

from fastapi import Request, status
from fastapi.responses import ORJSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings
from app.services.billing_monitor import send_slack_alert

logger = logging.getLogger(__name__)
settings = get_settings()

# 백그라운드 태스크 참조 보관 (GC 방지)
_background_tasks: set[asyncio.Task] = set()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """슬라이딩 윈도우 In-memory Rate Limiter (thread-safe)."""

    def __init__(self, app, limit: int = 60, window_seconds: int = 60) -> None:
        super().__init__(app)
        self.limit = limit
        self.window = window_seconds
        self._lock = threading.Lock()
        self._request_log: dict[str, deque] = {}
        self._last_cleanup = time.monotonic()
        self._cleanup_interval = 300  # 5분마다 정리

    def _cleanup_stale_entries(self, now: float) -> None:
        """비활성 IP 항목을 정리합니다 (메모리 누수 방지)."""
        if now - self._last_cleanup < self._cleanup_interval:
            return
        window_start = now - self.window
        stale_keys = [
            ip for ip, dq in self._request_log.items()
            if not dq or dq[-1] < window_start
        ]
        for key in stale_keys:
            del self._request_log[key]
        self._last_cleanup = now
        if stale_keys:
            logger.debug("Rate limiter cleanup: removed %d stale IPs", len(stale_keys))

    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/health":
            return await call_next(request)

        ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        window_start = now - self.window

        with self._lock:
            self._cleanup_stale_entries(now)

            if ip not in self._request_log:
                self._request_log[ip] = deque()
            dq = self._request_log[ip]

            while dq and dq[0] < window_start:
                dq.popleft()

            if len(dq) >= self.limit:
                logger.warning("Rate limit exceeded: ip=%s, path=%s", ip, request.url.path)
                try:
                    task = asyncio.create_task(send_slack_alert(
                        f":no_entry: *AudioScope 어뷰징 감지*\n"
                        f"- IP: `{ip}`\n"
                        f"- 경로: `{request.url.path}`\n"
                        f"- 제한: {self.limit}req/{self.window}s 초과"
                    ))
                    _background_tasks.add(task)
                    task.add_done_callback(_background_tasks.discard)
                except RuntimeError:
                    pass
                return ORJSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"success": False, "data": None, "error": "Too many requests. Please slow down."},
                    headers={"Retry-After": str(self.window)},
                )

            dq.append(now)

        return await call_next(request)
