"""
Google OAuth 서비스.
google-auth 라이브러리로 Google ID 토큰을 검증합니다.
"""

import logging

from fastapi import HTTPException
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def verify_google_token(token: str) -> dict:
    """Google OAuth ID 토큰을 검증하고 사용자 정보를 반환합니다.

    Returns:
        {
            "email": str,
            "name": str | None,
            "picture": str | None,
            "google_sub": str,   # Google 고유 사용자 ID
        }

    Raises:
        HTTPException 401: 토큰이 유효하지 않을 경우
        HTTPException 503: GOOGLE_CLIENT_ID 미설정 시 (production)
    """
    client_id = settings.GOOGLE_CLIENT_ID

    if not client_id:
        if settings.ENVIRONMENT == "production":
            raise HTTPException(
                status_code=503,
                detail="Google OAuth is not configured.",
            )
        # 개발 환경: 더미 데이터 반환
        logger.warning("GOOGLE_CLIENT_ID not set. Using dev mode Google token.")
        return {
            "email": "dev-google@audioscope.app",
            "name": "Dev Google User",
            "picture": None,
            "google_sub": f"dev_google_{token[:8]}",
        }

    try:
        id_info = google_id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            client_id,
        )
    except ValueError as exc:
        logger.warning("Google token verification failed: %s", exc)
        raise HTTPException(status_code=401, detail="Invalid Google ID token.")
    except Exception as exc:
        logger.error("Google token verification error: %s", exc)
        raise HTTPException(status_code=401, detail="Google token verification failed.")

    email: str | None = id_info.get("email")
    if not email:
        raise HTTPException(status_code=401, detail="Google token missing email claim.")

    email_verified: bool = id_info.get("email_verified", False)
    if not email_verified:
        raise HTTPException(status_code=401, detail="Google email is not verified.")

    return {
        "email": email,
        "name": id_info.get("name"),
        "picture": id_info.get("picture"),
        "google_sub": id_info.get("sub", ""),
    }
