"""
통일된 API 응답 헬퍼 모듈.
모든 API 응답을 {success, data, error} 포맷으로 반환합니다.
"""

from typing import Any

from fastapi.responses import ORJSONResponse


def success_response(data: Any = None, status_code: int = 200) -> ORJSONResponse:
    """성공 응답을 반환합니다."""
    return ORJSONResponse(
        status_code=status_code,
        content={"success": True, "data": data, "error": None},
    )


def error_response(error: str, status_code: int = 400) -> ORJSONResponse:
    """에러 응답을 반환합니다."""
    return ORJSONResponse(
        status_code=status_code,
        content={"success": False, "data": None, "error": error},
    )


def paginated_response(
    items: list[Any],
    total: int,
    page: int,
    size: int,
) -> ORJSONResponse:
    """페이지네이션 응답을 반환합니다."""
    return ORJSONResponse(
        status_code=200,
        content={
            "success": True,
            "data": {
                "items": items,
                "total": total,
                "page": page,
                "size": size,
                "has_next": (page * size) < total,
            },
            "error": None,
        },
    )
