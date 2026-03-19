"""
인증 유틸리티 모듈.
Firebase 토큰 검증, JWT 생성/검증, FastAPI 의존성.
"""

import base64
import json
import logging
from datetime import datetime, timedelta, timezone

import firebase_admin
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth as firebase_auth, credentials
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

import threading

_firebase_app: firebase_admin.App | None = None
_firebase_lock = threading.Lock()
_bearer_scheme = HTTPBearer(auto_error=False)


def init_firebase() -> None:
    """Firebase Admin SDK를 초기화합니다 (thread-safe)."""
    global _firebase_app
    if _firebase_app is not None:
        return
    with _firebase_lock:
        if _firebase_app is not None:
            return
    try:
        # 1순위: 환경변수로 전달된 base64 인코딩 JSON
        if settings.FIREBASE_CREDENTIALS_JSON:
            val = settings.FIREBASE_CREDENTIALS_JSON.strip()
            try:
                cred_dict = json.loads(val)
            except (json.JSONDecodeError, ValueError):
                cred_dict = json.loads(base64.b64decode(val))
            cred = credentials.Certificate(cred_dict)
        else:
            # 2순위: 파일 경로
            cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        _firebase_app = firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized.")
    except FileNotFoundError:
        logger.warning(
            "Firebase credentials file not found: %s. Firebase auth disabled.",
            settings.FIREBASE_CREDENTIALS_PATH,
        )
    except Exception as exc:
        logger.warning("Firebase init failed: %s. Firebase auth disabled.", exc)
        if settings.ENVIRONMENT == "production":
            raise RuntimeError(f"Firebase init failed in production: {exc}") from exc


def verify_firebase_token(token: str) -> dict:
    """Firebase ID 토큰을 검증합니다."""
    if _firebase_app is None:
        if settings.ENVIRONMENT == "production":
            raise HTTPException(status_code=503, detail="Auth service unavailable.")
        # Firebase 미설정 시 개발용 더미 데이터 반환
        logger.warning("Firebase not initialized. Using dev mode token.")
        return {
            "uid": f"dev_{token[:8]}",
            "email": "dev@audioscope.app",
            "name": "Dev User",
            "firebase": {"sign_in_provider": "google.com"},
        }
    try:
        decoded = firebase_auth.verify_id_token(token)
        return decoded
    except firebase_auth.ExpiredIdTokenError:
        raise HTTPException(status_code=401, detail="Firebase token expired.")
    except firebase_auth.InvalidIdTokenError:
        raise HTTPException(status_code=401, detail="Invalid Firebase token.")
    except Exception as exc:
        logger.error("Firebase token verification failed: %s", exc)
        raise HTTPException(status_code=401, detail="Token verification failed.")


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """JWT 액세스 토큰을 생성합니다 (기본 만료: 15분)."""
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {
        **data,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict | str, expires_delta: timedelta | None = None) -> str:
    """JWT 리프레시 토큰을 생성합니다 (기본 만료: 7일).

    data가 str이면 user_id로 간주하여 {"sub": data} 형태로 래핑합니다.
    """
    if isinstance(data, str):
        data = {"sub": data}
    if expires_delta is None:
        expires_delta = timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS)
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {
        **data,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


# 하위 호환성 유지 (기존 users.py 에서 create_jwt_token 사용)
def create_jwt_token(user_id: str) -> str:
    """JWT 액세스 토큰을 생성합니다 (하위 호환 래퍼)."""
    return create_access_token({"sub": user_id})


async def verify_refresh_token(token: str, db: AsyncSession) -> str:
    """DB에서 리프레시 토큰을 검증하고 user_id를 반환합니다.

    - JWT 서명 및 만료 검증
    - DB에서 존재 여부 및 revoked 상태 확인
    """
    from app.models.refresh_token import RefreshToken

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type.")
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload.")
    except JWTError as exc:
        logger.warning("Refresh token JWT validation failed: %s", exc)
        raise HTTPException(status_code=401, detail="Invalid refresh token.")

    stmt = select(RefreshToken).where(RefreshToken.token == token)
    result = await db.execute(stmt)
    db_token = result.scalar_one_or_none()

    if db_token is None:
        raise HTTPException(status_code=401, detail="Refresh token not found.")
    if db_token.revoked:
        raise HTTPException(status_code=401, detail="Refresh token has been revoked.")
    if db_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh token expired.")

    return user_id


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> str:
    """JWT 토큰에서 user_id를 추출합니다."""
    if creds is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(
            creds.credentials,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        if payload.get("type") != "access":
            raise JWTError("Invalid token type.")
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise JWTError("Missing subject.")
        return user_id
    except JWTError as exc:
        logger.warning("JWT validation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> str | None:
    """인증이 선택적인 엔드포인트용. 미인증 시 None 반환."""
    if creds is None:
        return None
    try:
        payload = jwt.decode(
            creds.credentials,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        if payload.get("type") != "access":
            return None
        return payload.get("sub")
    except JWTError:
        return None


async def refresh_access_token(refresh_token_str: str) -> str:
    """리프레시 토큰으로 새 액세스 토큰을 발급합니다 (DB 미검증, 하위 호환)."""
    try:
        payload = jwt.decode(
            refresh_token_str,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type.")
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token.")
        return create_jwt_token(user_id)
    except JWTError as exc:
        logger.warning("Refresh token validation failed: %s", exc)
        raise HTTPException(status_code=401, detail="Invalid refresh token.")
