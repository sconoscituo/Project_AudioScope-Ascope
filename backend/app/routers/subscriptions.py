"""
구독 관리 API 라우터.
프리미엄 구독 조회, 업그레이드, 취소를 제공합니다.
광고 시청 보상(무료 1회 추가 청취)도 포함합니다.
"""

import logging
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, get_redis
from app.models.listen_history import ListenHistory
from app.schemas.subscription import (
    SubscriptionCancelRequest,
    SubscriptionCreateRequest,
    SubscriptionResponse,
)
from app.services.subscription import (
    cancel_subscription,
    check_briefing_access,
    get_or_create_subscription,
    upgrade_subscription,
)
from app.utils.auth import get_current_user
from app.utils.response import error_response, success_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/subscriptions", tags=["subscriptions"])

FREE_DAILY_LISTENS = 1
AD_BONUS_LISTENS = 1


@router.get("/me")
async def get_my_subscription(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """현재 구독 상태를 반환합니다."""
    sub = await get_or_create_subscription(db, user_id)
    data = SubscriptionResponse.model_validate(sub).model_dump()
    data["is_active_premium"] = sub.is_active_premium

    # 오늘 무료 청취 잔여 횟수
    today_listens = await _get_today_listen_count(db, user_id)
    ad_bonus = await _get_ad_bonus_count(user_id)
    max_free = FREE_DAILY_LISTENS + ad_bonus

    data["free_listens_remaining"] = max(0, max_free - today_listens) if not sub.is_active_premium else -1
    data["ad_bonus_available"] = ad_bonus == 0  # 아직 광고 안 봤으면 true

    return success_response(data)


@router.post("/upgrade")
async def upgrade(
    body: SubscriptionCreateRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """프리미엄으로 업그레이드합니다."""
    if body.plan not in ("monthly", "yearly"):
        return error_response("Invalid plan. Use 'monthly' or 'yearly'.", 400)

    sub = await upgrade_subscription(
        db, user_id, body.plan, body.payment_provider, body.payment_id, body.price_krw
    )
    return success_response(SubscriptionResponse.model_validate(sub).model_dump())


@router.post("/cancel")
async def cancel(
    body: SubscriptionCancelRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """구독을 취소합니다."""
    sub = await cancel_subscription(db, user_id)
    return success_response({"message": "구독이 취소되었습니다. 만료일까지 이용 가능합니다."})


@router.post("/ad-reward")
async def claim_ad_reward(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    광고 시청 보상: 무료 계정에 오늘 1회 추가 청취권을 부여합니다.
    Redis에 당일 보상 여부를 기록합니다.
    """
    sub = await get_or_create_subscription(db, user_id)
    if sub.is_active_premium:
        return error_response("프리미엄 사용자는 광고 보상이 필요없습니다.", 400)

    redis = await get_redis()
    key = f"ad_reward:{user_id}:{date.today().isoformat()}"
    already_claimed = await redis.get(key)
    if already_claimed:
        return error_response("오늘은 이미 광고 보상을 받았습니다.", 400)

    # 보상 기록 (자정에 자동 만료)
    await redis.setex(key, 86400, "1")
    logger.info("Ad reward claimed: user=%s", user_id)

    return success_response({
        "message": "광고 보상이 적용되었습니다! 추가 1회 청취가 가능합니다.",
        "bonus_listens": AD_BONUS_LISTENS,
    })


@router.get("/access/{period}")
async def check_access(
    period: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """특정 시간대 브리핑 접근 가능 여부를 확인합니다."""
    can_access, reason = await check_briefing_access(db, user_id, period)

    # 무료 사용자 일일 청취 횟수 체크
    if can_access and reason == "free_period":
        today_listens = await _get_today_listen_count(db, user_id)
        ad_bonus = await _get_ad_bonus_count(user_id)
        if today_listens >= FREE_DAILY_LISTENS + ad_bonus:
            can_access = False
            reason = "daily_limit_reached"

    return success_response({
        "can_access": can_access,
        "reason": reason,
    })


async def _get_today_listen_count(db: AsyncSession, user_id: str) -> int:
    """오늘 사용자의 청취 횟수를 반환합니다."""
    today = date.today()
    stmt = select(func.count()).select_from(ListenHistory).where(
        ListenHistory.user_id == user_id,
        func.date(ListenHistory.listened_at) == today,
    )
    result = await db.execute(stmt)
    return result.scalar_one() or 0


async def _get_ad_bonus_count(user_id: str) -> int:
    """오늘 광고 보상 횟수를 반환합니다."""
    try:
        redis = await get_redis()
        key = f"ad_reward:{user_id}:{date.today().isoformat()}"
        result = await redis.get(key)
        return int(result) if result else 0
    except Exception:
        return 0
