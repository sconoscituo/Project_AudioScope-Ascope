"""
관리자 API 라우터.
수동 브리핑 생성 트리거, 빌링 현황 조회, 상세 헬스체크를 제공합니다.
"""

import logging
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.billing import BillingUsage
from app.models.briefing import Briefing
from app.scheduler.tasks import generate_briefing

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

VALID_PERIODS = {"morning", "lunch", "evening"}


def _success(data: Any) -> dict:
    """통일된 성공 응답 포맷을 반환합니다."""
    return {"success": True, "data": data, "error": None}


@router.post("/briefings/generate")
async def trigger_briefing_generation(
    period: str = Query(..., description="morning / lunch / evening"),
    target_date: date = Query(default=None, description="생성 대상 날짜 (기본: 오늘)"),
) -> dict:
    """
    특정 기간의 브리핑 생성을 수동으로 트리거합니다.

    Args:
        period: 브리핑 기간
        target_date: 대상 날짜 (기본값: 오늘)

    Returns:
        dict: 생성 작업 시작 결과
    """
    if period not in VALID_PERIODS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid period. Must be one of: {', '.join(VALID_PERIODS)}",
        )

    logger.info("Manual briefing generation triggered: period=%s", period)
    # 백그라운드에서 실행 (실제 운영에서는 BackgroundTasks 활용 가능)
    import asyncio
    asyncio.create_task(generate_briefing(period))
    return _success({"message": f"Briefing generation started for period='{period}'."})


@router.get("/billing")
async def get_billing_status(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    오늘의 Gemini 사용량과 이번 달 Supertone 사용량을 반환합니다.

    Returns:
        dict: 서비스별 비용 및 요청 수
    """
    today = date.today()
    month_start = date(today.year, today.month, 1)

    # Gemini 일일 사용량
    gemini_stmt = select(
        func.sum(BillingUsage.amount_usd).label("total_usd"),
        func.sum(BillingUsage.request_count).label("total_requests"),
    ).where(
        BillingUsage.service == "gemini",
        BillingUsage.usage_date == today,
    )
    gemini_result = await db.execute(gemini_stmt)
    gemini_row = gemini_result.one()

    # Supertone 월간 사용량
    supertone_stmt = select(
        func.sum(BillingUsage.amount_usd).label("total_usd"),
        func.sum(BillingUsage.request_count).label("total_requests"),
    ).where(
        BillingUsage.service == "supertone",
        BillingUsage.usage_date >= month_start,
        BillingUsage.usage_date <= today,
    )
    supertone_result = await db.execute(supertone_stmt)
    supertone_row = supertone_result.one()

    from app.config import get_settings
    settings = get_settings()

    data = {
        "gemini": {
            "period": "daily",
            "date": today.isoformat(),
            "total_usd": float(gemini_row.total_usd or 0),
            "total_requests": int(gemini_row.total_requests or 0),
            "limit_usd": settings.GEMINI_DAILY_LIMIT_USD,
            "exceeded": float(gemini_row.total_usd or 0) >= settings.GEMINI_DAILY_LIMIT_USD,
        },
        "supertone": {
            "period": "monthly",
            "month": f"{today.year}-{today.month:02d}",
            "total_usd": float(supertone_row.total_usd or 0),
            "total_requests": int(supertone_row.total_requests or 0),
            "limit_usd": settings.SUPERTONE_MONTHLY_LIMIT_USD,
            "exceeded": float(supertone_row.total_usd or 0) >= settings.SUPERTONE_MONTHLY_LIMIT_USD,
        },
    }
    logger.info("Billing status fetched: gemini=$%.4f, supertone=$%.4f",
                data["gemini"]["total_usd"], data["supertone"]["total_usd"])
    return _success(data)


@router.get("/health")
async def detailed_health(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    DB 연결, 최근 브리핑 상태, 스케줄러 상태를 포함한 상세 헬스체크를 반환합니다.

    Returns:
        dict: 시스템 각 컴포넌트의 상태
    """
    # DB 연결 확인
    db_ok = False
    try:
        await db.execute(select(1))
        db_ok = True
    except Exception as exc:
        logger.error("DB health check failed: %s", exc)

    # 최근 브리핑 상태
    today = date.today()
    stmt = select(Briefing).where(Briefing.scheduled_date == today)
    result = await db.execute(stmt)
    today_briefings = result.scalars().all()
    briefing_status = {
        b.period: b.status for b in today_briefings
    }

    # 스케줄러 상태
    from app.scheduler.tasks import scheduler
    scheduler_running = scheduler.running

    data = {
        "database": "ok" if db_ok else "error",
        "scheduler": "running" if scheduler_running else "stopped",
        "today_briefings": briefing_status,
    }
    logger.info("Detailed health check: db=%s, scheduler=%s", data["database"], data["scheduler"])
    return _success(data)
