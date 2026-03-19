"""
사용자 API 라우터.
인증, 프로필, 카테고리 선호도, 문의하기를 제공합니다.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
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
    VoiceUpdateRequest,
)
from app.services.billing_monitor import send_inquiry_alert
from app.utils.auth import create_jwt_token, create_refresh_token, get_current_user, refresh_access_token, verify_firebase_token
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

        # 추천 코드 생성
        import hashlib
        user.referral_code = hashlib.sha256(str(user.id).encode()).hexdigest()[:8].upper()
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

    access_token = create_jwt_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))
    categories = [p.category for p in user.category_preferences if p.is_enabled]

    user_data = UserResponse.model_validate(user).model_dump()
    user_data["categories"] = categories

    return success_response({
        "access_token": access_token,
        "refresh_token": refresh_token,
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


@router.patch("/me/preferences")
async def update_preferences(
    preferred_categories: list[str] | None = None,
    briefing_times: list[str] | None = None,
    notification_enabled: bool | None = None,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """사용자 선호도(카테고리, 브리핑 시간대, 알림 여부)를 업데이트합니다."""
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    VALID_CATEGORIES = set(NEWS_CATEGORIES.keys())
    VALID_TIMES = {"morning", "lunch", "evening", "night"}

    if preferred_categories is not None:
        filtered = [c for c in preferred_categories if c in VALID_CATEGORIES]
        if not filtered:
            return error_response("유효한 카테고리를 1개 이상 입력하세요.", status_code=400)
        user.preferred_categories = filtered
    if briefing_times is not None:
        filtered_times = [t for t in briefing_times if t in VALID_TIMES]
        user.briefing_times = filtered_times if filtered_times else user.briefing_times
    if notification_enabled is not None:
        user.notification_enabled = notification_enabled

    await db.flush()
    return success_response({
        "message": "설정 업데이트 완료",
        "preferred_categories": user.preferred_categories,
        "briefing_times": user.briefing_times,
        "notification_enabled": user.notification_enabled,
    })


class FcmTokenRequest(BaseModel):
    fcm_token: str = Field(..., min_length=1, max_length=512)


@router.put("/me/fcm-token")
async def update_fcm_token(
    body: FcmTokenRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """FCM 디바이스 토큰을 등록/갱신합니다."""
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    user.fcm_token = body.fcm_token
    await db.flush()
    logger.info("FCM token updated: user=%s", user_id)
    return success_response({"message": "FCM 토큰이 등록되었습니다."})


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


SUPERTONE_VOICES = [
    {"id": "ko-KR-female-1", "name": "지수 (차분한 여성)", "gender": "female", "style": "calm"},
    {"id": "ko-KR-female-2", "name": "하린 (밝은 여성)", "gender": "female", "style": "bright"},
    {"id": "ko-KR-male-1", "name": "준호 (차분한 남성)", "gender": "male", "style": "calm"},
    {"id": "ko-KR-male-2", "name": "민준 (힘찬 남성)", "gender": "male", "style": "energetic"},
]


@router.get("/voices")
async def get_voices():
    return success_response(data=SUPERTONE_VOICES)


@router.patch("/me/voice")
async def update_voice(
    body: VoiceUpdateRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    valid_ids = [v["id"] for v in SUPERTONE_VOICES]
    if body.voice_id not in valid_ids:
        raise HTTPException(status_code=400, detail="Invalid voice_id")
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.preferred_voice_id = body.voice_id
    return success_response(data={"voice_id": body.voice_id})


class InquiryRequest(BaseModel):
    subject: str = Field(..., max_length=200)
    message: str = Field(..., max_length=2000)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post("/auth/refresh")
async def refresh_token(body: RefreshTokenRequest):
    """리프레시 토큰으로 새 액세스 토큰을 발급합니다."""
    new_access = await refresh_access_token(body.refresh_token)
    return success_response({
        "access_token": new_access,
        "token_type": "bearer",
    })


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
