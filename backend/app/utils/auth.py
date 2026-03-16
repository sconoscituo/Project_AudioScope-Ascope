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

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_firebase_app: firebase_admin.App | None = None
_bearer_scheme = HTTPBearer(auto_error=False)


def init_firebase() -> None:
    """Firebase Admin SDK를 초기화합니다."""
    global _firebase_app
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


def create_jwt_token(user_id: str) -> str:
    """JWT 액세스 토큰을 생성합니다."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """JWT 리프레시 토큰을 생성합니다."""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


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
        return payload.get("sub")
    except JWTError:
        return None
