"""
사용자 API 라우터.
Firebase 토큰 기반 로그인/회원가입, 내 정보 조회, 회원탈퇴를 제공합니다.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.utils.auth import create_jwt_token, get_current_user, verify_firebase_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/users", tags=["users"])


def _success(data: Any) -> dict:
    """통일된 성공 응답 포맷을 반환합니다."""
    return {"success": True, "data": data, "error": None}


@router.post("/auth")
async def authenticate(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Firebase ID 토큰으로 로그인하거나 신규 회원을 등록합니다.

    Args:
        body: Firebase ID 토큰 포함 요청 바디

    Returns:
        dict: JWT 액세스 토큰 및 사용자 정보
    """
    decoded = verify_firebase_token(body.firebase_token)
    firebase_uid: str = decoded["uid"]
    email: str | None = decoded.get("email")
    display_name: str | None = decoded.get("name")
    provider: str = decoded.get("firebase", {}).get("sign_in_provider", "unknown")

    # provider 정규화 (google.com -> google)
    if "google" in provider:
        provider = "google"
    elif "apple" in provider:
        provider = "apple"
    elif "kakao" in provider or "oidc" in provider:
        provider = "kakao"

    stmt = select(User).where(User.firebase_uid == firebase_uid)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            firebase_uid=firebase_uid,
            email=email,
            display_name=display_name,
            provider=provider,
        )
        db.add(user)
        await db.flush()
        logger.info("New user registered: uid=%s, provider=%s", firebase_uid, provider)
    else:
        user.last_login_at = datetime.now(timezone.utc)
        if display_name and not user.display_name:
            user.display_name = display_name
        logger.info("User logged in: id=%s, provider=%s", user.id, provider)

    await db.commit()
    await db.refresh(user)

    token = create_jwt_token(str(user.id))
    return _success({
        "access_token": token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user).model_dump(),
    })


@router.get("/me")
async def get_me(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    현재 로그인한 사용자의 정보를 반환합니다.

    Returns:
        dict: 사용자 정보
    """
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    logger.info("User info fetched: id=%s", user_id)
    return _success(UserResponse.model_validate(user).model_dump())


@router.delete("/me")
async def delete_me(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    현재 로그인한 사용자의 계정을 비활성화합니다 (소프트 삭제).

    Returns:
        dict: 탈퇴 처리 결과
    """
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    user.is_active = False
    await db.commit()
    logger.info("User deactivated: id=%s", user_id)
    return _success({"message": "Account deactivated successfully."})
