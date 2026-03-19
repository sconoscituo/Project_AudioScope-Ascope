"""
인증 API 라우터.
JWT refresh token 기반 로그인/로그아웃/갱신 및 Google OAuth 로그인을 제공합니다.
"""

import hashlib
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.database import get_db
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserCategoryPreference
from app.schemas.user import UserResponse
from app.services.oauth import verify_google_token
from app.utils.auth import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    get_current_user,
)
from app.utils.response import success_response, error_response

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


# ── Request / Response Schemas ──────────────────────────────────────────────

class LoginRequest(BaseModel):
    """이메일/비밀번호 로그인 요청 (Firebase 우선 사용; 직접 로그인 예비용)."""
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class GoogleLoginRequest(BaseModel):
    id_token: str


# ── 내부 헬퍼 ───────────────────────────────────────────────────────────────

async def _issue_tokens(user: User, db: AsyncSession) -> dict:
    """access_token + refresh_token 을 발급하고 DB에 refresh_token을 저장합니다."""
    user_id_str = str(user.id)
    access_token = create_access_token({"sub": user_id_str})
    refresh_token_str = create_refresh_token({"sub": user_id_str})

    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS)
    db_token = RefreshToken(
        user_id=user.id,
        token=refresh_token_str,
        expires_at=expires_at,
    )
    db.add(db_token)
    await db.flush()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token_str,
        "token_type": "bearer",
    }


async def _get_or_create_user_by_google(
    email: str,
    name: str | None,
    picture: str | None,
    google_sub: str,
    db: AsyncSession,
) -> tuple[User, bool]:
    """Google 정보로 기존 유저를 찾거나 신규 가입시킵니다."""
    # 1) firebase_uid = "google:{google_sub}" 로 조회 (Google OAuth 전용 uid 규칙)
    firebase_uid = f"google:{google_sub}"
    stmt = (
        select(User)
        .where(User.firebase_uid == firebase_uid)
        .options(selectinload(User.category_preferences))
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is not None:
        user.last_login_at = datetime.now(timezone.utc)
        if name and not user.display_name:
            user.display_name = name
        if picture and not user.profile_image_url:
            user.profile_image_url = picture
        await db.flush()
        return user, False

    # 2) 이메일로 기존 유저 조회 (Firebase 등록 이력 있을 수 있음)
    if email:
        stmt_email = (
            select(User)
            .where(User.email == email)
            .options(selectinload(User.category_preferences))
        )
        result_email = await db.execute(stmt_email)
        existing = result_email.scalar_one_or_none()
        if existing is not None:
            # firebase_uid 업데이트 후 로그인 처리
            if not existing.firebase_uid or existing.firebase_uid.startswith("dev_"):
                existing.firebase_uid = firebase_uid
            existing.last_login_at = datetime.now(timezone.utc)
            await db.flush()
            return existing, False

    # 3) 신규 가입
    user = User(
        firebase_uid=firebase_uid,
        email=email,
        display_name=name,
        provider="google",
        profile_image_url=picture,
    )
    db.add(user)
    await db.flush()

    user.referral_code = hashlib.sha256(str(user.id).encode()).hexdigest()[:8].upper()
    await db.flush()

    default_cats = ["politics", "economy", "society", "world", "tech", "science"]
    for i, cat in enumerate(default_cats):
        pref = UserCategoryPreference(
            user_id=user.id, category=cat, is_enabled=True, priority=i
        )
        db.add(pref)
    await db.flush()
    await db.refresh(user, ["category_preferences"])

    logger.info("New user via Google OAuth: uid=%s, email=%s", firebase_uid, email)
    return user, True


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/google")
async def google_login(
    body: GoogleLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Google OAuth ID 토큰 검증 후 로그인/회원가입합니다.

    Flutter 앱에서 google_sign_in 패키지로 획득한 idToken을 전달합니다.
    """
    info = await verify_google_token(body.id_token)

    user, is_new = await _get_or_create_user_by_google(
        email=info["email"],
        name=info.get("name"),
        picture=info.get("picture"),
        google_sub=info["google_sub"],
        db=db,
    )

    tokens = await _issue_tokens(user, db)

    categories = [p.category for p in user.category_preferences if p.is_enabled]
    user_data = UserResponse.model_validate(user).model_dump()
    user_data["categories"] = categories

    return success_response({
        **tokens,
        "is_new_user": is_new,
        "user": user_data,
    })


@router.post("/refresh")
async def refresh_token(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """리프레시 토큰으로 새 액세스 토큰을 발급합니다.

    - JWT 서명/만료 검증
    - DB에서 revoked 여부 확인
    - 새 access_token 반환 (refresh_token은 유지)
    """
    user_id = await verify_refresh_token(body.refresh_token, db)
    new_access = create_access_token({"sub": user_id})

    return success_response({
        "access_token": new_access,
        "token_type": "bearer",
    })


@router.post("/logout")
async def logout(
    body: LogoutRequest,
    db: AsyncSession = Depends(get_db),
):
    """리프레시 토큰을 폐기(revoke)하여 로그아웃합니다."""
    stmt = select(RefreshToken).where(RefreshToken.token == body.refresh_token)
    result = await db.execute(stmt)
    db_token = result.scalar_one_or_none()

    if db_token is None:
        # 이미 없거나 만료된 토큰 — 멱등성 보장
        return success_response({"message": "Logged out."})

    db_token.revoked = True
    await db.flush()

    logger.info("Refresh token revoked: user=%s", db_token.user_id)
    return success_response({"message": "Logged out."})


@router.post("/logout/all")
async def logout_all(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """해당 유저의 모든 리프레시 토큰을 일괄 폐기합니다 (전체 기기 로그아웃)."""
    from sqlalchemy import update as sa_update
    from app.models.refresh_token import RefreshToken as RT

    await db.execute(
        sa_update(RT)
        .where(RT.user_id == user_id, RT.revoked.is_(False))
        .values(revoked=True)
    )
    await db.flush()

    logger.info("All refresh tokens revoked for user: %s", user_id)
    return success_response({"message": "All sessions logged out."})
