"""
관리자 API 라우터.
수동 브리핑 생성, 빌링 현황, 상세 헬스체크, 시스템 통계를 제공합니다.
"""

import asyncio
import logging
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.billing import BillingUsage
from app.models.briefing import Briefing
from app.models.listen_history import ListenHistory
from app.models.user import User
from app.scheduler.tasks import generate_briefing
from app.utils.auth import get_current_user
from app.utils.response import success_response

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

VALID_PERIODS = {"morning", "lunch", "evening"}


async def admin_required(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> str:
    """관리자 권한을 확인합니다."""
    stmt = select(User).where(User.id == user_id)
    user = (await db.execute(stmt)).scalar_one_or_none()
    if user is None or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required.")
    return user_id


@router.post("/briefings/generate")
async def trigger_briefing_generation(
    period: str = Query(..., description="morning / lunch / evening"),
    _: str = Depends(admin_required),
):
    """브리핑 생성을 수동으로 트리거합니다."""
    if period not in VALID_PERIODS:
        raise HTTPException(status_code=400, detail=f"Invalid period: {period}")

    asyncio.create_task(generate_briefing(period))
    return success_response({"message": f"Briefing generation started: {period}"})


@router.get("/billing")
async def get_billing_status(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(admin_required),
):
    """빌링 현황을 반환합니다."""
    today = date.today()
    month_start = date(today.year, today.month, 1)

    gemini_stmt = select(
        func.sum(BillingUsage.amount_usd).label("total_usd"),
        func.sum(BillingUsage.request_count).label("total_requests"),
    ).where(BillingUsage.service == "gemini", BillingUsage.usage_date == today)
    gemini = (await db.execute(gemini_stmt)).one()

    supertone_stmt = select(
        func.sum(BillingUsage.amount_usd).label("total_usd"),
        func.sum(BillingUsage.request_count).label("total_requests"),
    ).where(
        BillingUsage.service == "supertone",
        BillingUsage.usage_date >= month_start,
    )
    supertone = (await db.execute(supertone_stmt)).one()

    return success_response({
        "gemini": {
            "period": "daily",
            "total_usd": float(gemini.total_usd or 0),
            "total_requests": int(gemini.total_requests or 0),
            "limit_usd": settings.GEMINI_DAILY_LIMIT_USD,
            "exceeded": float(gemini.total_usd or 0) >= settings.GEMINI_DAILY_LIMIT_USD,
        },
        "supertone": {
            "period": "monthly",
            "total_usd": float(supertone.total_usd or 0),
            "total_requests": int(supertone.total_requests or 0),
            "limit_usd": settings.SUPERTONE_MONTHLY_LIMIT_USD,
            "exceeded": float(supertone.total_usd or 0) >= settings.SUPERTONE_MONTHLY_LIMIT_USD,
        },
    })


@router.get("/stats")
async def get_system_stats(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(admin_required),
):
    """시스템 통계를 반환합니다."""
    total_users = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    active_users = (await db.execute(
        select(func.count()).select_from(User).where(User.is_active.is_(True))
    )).scalar_one()
    premium_users = (await db.execute(
        select(func.count()).select_from(User).where(User.is_premium.is_(True))
    )).scalar_one()
    total_briefings = (await db.execute(
        select(func.count()).select_from(Briefing).where(Briefing.status == "completed")
    )).scalar_one()
    total_listens = (await db.execute(
        select(func.count()).select_from(ListenHistory)
    )).scalar_one()

    return success_response({
        "users": {"total": total_users, "active": active_users, "premium": premium_users},
        "briefings": {"total_completed": total_briefings},
        "listens": {"total": total_listens},
    })


@router.get("/health")
async def detailed_health(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(admin_required),
):
    """상세 헬스체크를 반환합니다."""
    db_ok = False
    try:
        await db.execute(select(1))
        db_ok = True
    except Exception as exc:
        logger.error("DB health check failed: %s", exc)

    today = date.today()
    stmt = select(Briefing).where(Briefing.scheduled_date == today)
    today_briefings = (await db.execute(stmt)).scalars().all()
    briefing_status = {b.period: b.status for b in today_briefings}

    from app.scheduler.tasks import scheduler
    scheduler_running = scheduler.running

    redis_ok = False
    try:
        from app.database import get_redis
        redis = await get_redis()
        await redis.ping()
        redis_ok = True
    except Exception:
        pass

    return success_response({
        "database": "ok" if db_ok else "error",
        "redis": "ok" if redis_ok else "error",
        "scheduler": "running" if scheduler_running else "stopped",
        "today_briefings": briefing_status,
        "environment": settings.ENVIRONMENT,
    })
