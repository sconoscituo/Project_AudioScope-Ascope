"""
인증 유틸리티 모듈.
Firebase 토큰 검증, JWT 생성/검증, FastAPI 의존성을 제공합니다.
"""

import logging
from datetime import datetime, timedelta, timezone

import firebase_admin
from firebase_admin import auth as firebase_auth, credentials
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_firebase_app: firebase_admin.App | None = None
_bearer_scheme = HTTPBearer()


def init_firebase() -> None:
    """
    Firebase Admin SDK를 초기화합니다. 앱 시작 시 1회 호출합니다.
    이미 초기화된 경우 무시합니다.
    """
    global _firebase_app
    if _firebase_app is not None:
        logger.info("Firebase already initialized, skipping.")
        return
    try:
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        _firebase_app = firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized successfully.")
    except Exception as exc:
        logger.error("Failed to initialize Firebase: %s", exc, exc_info=True)
        raise


def verify_firebase_token(token: str) -> dict:
    """
    Firebase ID 토큰을 검증하고 디코딩된 payload를 반환합니다.

    Args:
        token: Firebase ID 토큰 문자열

    Returns:
        dict: 디코딩된 토큰 payload (uid, email, sign_in_provider 등 포함)

    Raises:
        HTTPException: 토큰이 유효하지 않거나 만료된 경우
    """
    try:
        decoded = firebase_auth.verify_id_token(token)
        logger.info("Firebase token verified for uid: %s", decoded.get("uid"))
        return decoded
    except firebase_auth.ExpiredIdTokenError:
        logger.warning("Firebase token expired.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firebase token has expired.",
        )
    except firebase_auth.InvalidIdTokenError as exc:
        logger.warning("Invalid Firebase token: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase token.",
        )
    except Exception as exc:
        logger.error("Firebase token verification failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed.",
        )


def create_jwt_token(user_id: str) -> str:
    """
    사용자 ID를 포함한 JWT 액세스 토큰을 생성합니다.

    Args:
        user_id: UUID 형식의 사용자 ID 문자열

    Returns:
        str: 서명된 JWT 토큰 문자열
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    logger.info("JWT token created for user_id: %s, expires_at: %s", user_id, expire)
    return token


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> str:
    """
    FastAPI 의존성: Authorization 헤더의 JWT 토큰을 검증하고 user_id를 반환합니다.

    Args:
        credentials: HTTP Bearer 인증 정보

    Returns:
        str: 검증된 사용자 ID

    Raises:
        HTTPException: 토큰이 유효하지 않거나 만료된 경우
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise JWTError("Missing subject claim.")
        logger.debug("JWT validated for user_id: %s", user_id)
        return user_id
    except JWTError as exc:
        logger.warning("JWT validation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )
