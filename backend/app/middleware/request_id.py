"""
Request ID 미들웨어.
모든 요청에 고유한 correlation_id를 부여하여 로그 추적을 지원합니다.
"""

import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.utils.logger import correlation_id_var


class RequestIdMiddleware(BaseHTTPMiddleware):
    """모든 요청에 X-Request-ID 헤더를 부여하는 미들웨어."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
        correlation_id_var.set(request_id)

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
