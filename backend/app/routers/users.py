"""
사용자 API 라우터.
인증, 프로필, 카테고리 선호도, 문의하기를 제공합니다.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.user import User, UserCategoryPreference, NEWS_CATEGORIES
from app.schemas.user import (
    CategoryUpdateRequest,
    UserCreate,
    UserResponse,
    UserUpdateRequest,
)
from app.services.billing_monitor import send_inquiry_alert
from app.utils.auth import create_jwt_token, get_current_user, verify_firebase_token
from app.utils.response import success_response, error_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.post("/auth")
async def authenticate(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """Firebase ID 토큰으로 로그인/회원가입하고 JWT를 발급합니다."""
    decoded = verify_firebase_token(body.firebase_token)
    firebase_uid: str = decoded["uid"]
    email: str | None = decoded.get("email")
    display_name: str | None = decoded.get("name")
    photo_url: str | None = decoded.get("picture")
    provider: str = decoded.get("firebase", {}).get("sign_in_provider", "unknown")

    # provider 정규화
    if "google" in provider:
        provider = "google"
    elif "apple" in provider:
        provider = "apple"
    elif "kakao" in provider or "oidc" in provider:
        provider = "kakao"

    stmt = select(User).where(User.firebase_uid == firebase_uid).options(
        selectinload(User.category_preferences)
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    is_new = False
    if user is None:
        user = User(
            firebase_uid=firebase_uid,
            email=email,
            display_name=display_name,
            provider=provider,
            profile_image_url=photo_url,
        )
        db.add(user)
        await db.flush()

        # 기본 카테고리 설정 (연예 제외)
        default_cats = ["politics", "economy", "society", "world", "tech", "science"]
        for i, cat in enumerate(default_cats):
            pref = UserCategoryPreference(
                user_id=user.id, category=cat, is_enabled=True, priority=i
            )
            db.add(pref)
        await db.flush()
        is_new = True
        logger.info("New user: uid=%s, provider=%s", firebase_uid, provider)
    else:
        user.last_login_at = datetime.now(timezone.utc)
        if display_name and not user.display_name:
            user.display_name = display_name
        if photo_url and not user.profile_image_url:
            user.profile_image_url = photo_url
        logger.info("User login: id=%s", user.id)

    await db.flush()
    await db.refresh(user)

    token = create_jwt_token(str(user.id))
    categories = [p.category for p in user.category_preferences if p.is_enabled]

    user_data = UserResponse.model_validate(user).model_dump()
    user_data["categories"] = categories

    return success_response({
        "access_token": token,
        "token_type": "bearer",
        "is_new_user": is_new,
        "user": user_data,
    })


@router.get("/me")
async def get_me(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """현재 로그인한 사용자 정보를 반환합니다."""
    stmt = (
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.category_preferences))
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    data = UserResponse.model_validate(user).model_dump()
    data["categories"] = [p.category for p in user.category_preferences if p.is_enabled]
    return success_response(data)


@router.patch("/me")
async def update_me(
    body: UserUpdateRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """사용자 정보를 수정합니다."""
    stmt = select(User).where(User.id == user_id)
    user = (await db.execute(stmt)).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    if body.display_name is not None:
        user.display_name = body.display_name
    if body.fcm_token is not None:
        user.fcm_token = body.fcm_token

    await db.flush()
    return success_response({"updated": True})


@router.put("/me/categories")
async def update_categories(
    body: CategoryUpdateRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """사용자 뉴스 카테고리 선호도를 업데이트합니다."""
    # 유효한 카테고리만 필터
    valid = [c for c in body.categories if c in NEWS_CATEGORIES]
    if not valid:
        return error_response("최소 1개 카테고리를 선택하세요.", status_code=400)

    # 기존 삭제 후 재생성 (원자적)
    await db.execute(
        delete(UserCategoryPreference).where(
            UserCategoryPreference.user_id == user_id
        )
    )
    for i, cat in enumerate(valid):
        pref = UserCategoryPreference(
            user_id=user_id, category=cat, is_enabled=True, priority=i
        )
        db.add(pref)

    await db.flush()
    return success_response({"categories": valid})


@router.get("/me/categories")
async def get_categories(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """사용자 카테고리 선호도를 반환합니다."""
    stmt = (
        select(UserCategoryPreference)
        .where(UserCategoryPreference.user_id == user_id, UserCategoryPreference.is_enabled.is_(True))
        .order_by(UserCategoryPreference.priority)
    )
    prefs = (await db.execute(stmt)).scalars().all()
    return success_response({
        "categories": [p.category for p in prefs],
        "available": NEWS_CATEGORIES,
    })


@router.delete("/me")
async def delete_me(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """계정을 비활성화합니다 (소프트 삭제)."""
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    user.is_active = False
    await db.flush()
    logger.info("User deactivated: id=%s", user_id)
    return success_response({"message": "Account deactivated."})


class InquiryRequest(BaseModel):
    subject: str
    message: str


@router.post("/me/inquiry")
async def submit_inquiry(
    body: InquiryRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """고객 문의를 Slack으로 전송합니다."""
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    email = user.email if user else "unknown"

    await send_inquiry_alert(email, str(user_id), body.subject, body.message)
    logger.info("Inquiry submitted: user=%s, subject=%s", user_id, body.subject)
    return success_response({"message": "문의가 접수되었습니다."})
