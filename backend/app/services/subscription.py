"""
구독 관리 서비스.
프리미엄 구독 생성/확인/취소, 프리미엄 접근 권한 검증을 담당합니다.
아침 브리핑은 무료, 점심/저녁은 프리미엄 전용입니다.
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.subscription import Subscription
from app.models.user import User

logger = logging.getLogger(__name__)
settings = get_settings()


async def get_or_create_subscription(
    db: AsyncSession, user_id: str
) -> Subscription:
    """사용자의 구독 정보를 조회하거나 무료 구독을 생성합니다."""
    stmt = select(Subscription).where(Subscription.user_id == user_id)
    result = await db.execute(stmt)
    sub = result.scalar_one_or_none()

    if sub is None:
        sub = Subscription(user_id=user_id, plan="free", status="active")
        db.add(sub)
        await db.flush()
        logger.info("Created free subscription for user %s", user_id)

    return sub


async def check_briefing_access(
    db: AsyncSession, user_id: str, period: str
) -> tuple[bool, str]:
    """
    사용자가 해당 시간대 브리핑에 접근 가능한지 확인합니다.

    Returns:
        tuple[bool, str]: (접근 가능 여부, 사유)
    """
    # 아침 브리핑은 항상 무료
    if period == settings.FREE_BRIEFING_PERIOD:
        return True, "free_period"

    sub = await get_or_create_subscription(db, user_id)

    if sub.is_active_premium:
        return True, "premium"

    # 트라이얼 기간 체크
    if sub.plan == "trial" and sub.status == "active":
        if sub.expires_at and sub.expires_at > datetime.now(timezone.utc):
            return True, "trial"

    return False, "premium_required"


async def upgrade_subscription(
    db: AsyncSession,
    user_id: str,
    plan: str,
    payment_provider: str,
    payment_id: str,
    price_krw: int,
) -> Subscription:
    """구독을 프리미엄으로 업그레이드합니다."""
    sub = await get_or_create_subscription(db, user_id)

    now = datetime.now(timezone.utc)
    if plan == "monthly":
        expires_at = now + timedelta(days=30)
    elif plan == "yearly":
        expires_at = now + timedelta(days=365)
    elif plan == "trial":
        expires_at = now + timedelta(days=settings.TRIAL_DAYS)
    else:
        raise ValueError(f"Invalid plan: {plan}")

    sub.plan = plan
    sub.status = "active"
    sub.started_at = now
    sub.expires_at = expires_at
    sub.payment_provider = payment_provider
    sub.payment_id = payment_id
    sub.price_krw = price_krw

    # 유저 프리미엄 상태 업데이트
    user_stmt = select(User).where(User.id == user_id)
    user_result = await db.execute(user_stmt)
    user = user_result.scalar_one_or_none()
    if user:
        user.is_premium = True

    await db.flush()
    logger.info("Subscription upgraded: user=%s, plan=%s, expires=%s", user_id, plan, expires_at)
    return sub


async def cancel_subscription(db: AsyncSession, user_id: str) -> Subscription:
    """구독을 취소합니다 (만료일까지 유지)."""
    sub = await get_or_create_subscription(db, user_id)
    sub.status = "cancelled"
    sub.cancelled_at = datetime.now(timezone.utc)
    await db.flush()
    logger.info("Subscription cancelled: user=%s", user_id)
    return sub


async def check_expired_subscriptions(db: AsyncSession) -> int:
    """만료된 구독을 일괄 처리합니다. 스케줄러에서 호출."""
    now = datetime.now(timezone.utc)
    stmt = select(Subscription).where(
        Subscription.status == "active",
        Subscription.plan != "free",
        Subscription.expires_at < now,
    )
    result = await db.execute(stmt)
    expired_subs = result.scalars().all()

    count = 0
    for sub in expired_subs:
        sub.status = "expired"
        sub.plan = "free"
        # 유저 프리미엄 해제
        user_stmt = select(User).where(User.id == sub.user_id)
        user_result = await db.execute(user_stmt)
        user = user_result.scalar_one_or_none()
        if user:
            user.is_premium = False
        count += 1

    if count:
        await db.flush()
        logger.info("Expired %d subscriptions", count)
    return count
