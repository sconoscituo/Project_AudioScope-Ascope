"""
브리핑 API 라우터.
오늘의 브리핑 조회, 특정 기간 브리핑 상세, 히스토리 조회를 제공합니다.
"""

import logging
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.briefing import Briefing
from app.schemas.briefing import BriefingListResponse, BriefingResponse
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/briefings", tags=["briefings"])

VALID_PERIODS = {"morning", "lunch", "evening"}


def _success(data: Any) -> dict:
    """통일된 성공 응답 포맷을 반환합니다."""
    return {"success": True, "data": data, "error": None}


@router.get("/today")
async def get_today_briefings(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """
    오늘의 브리핑 목록(morning/lunch/evening)을 반환합니다.

    Returns:
        dict: success/data/error 포맷의 오늘 브리핑 목록
    """
    today = date.today()
    stmt = (
        select(Briefing)
        .where(Briefing.scheduled_date == today)
        .options(selectinload(Briefing.articles))
        .order_by(Briefing.period)
    )
    result = await db.execute(stmt)
    briefings = result.scalars().all()
    logger.info("Fetched %d briefings for today (%s)", len(briefings), today)
    data = [BriefingResponse.model_validate(b) for b in briefings]
    return _success([d.model_dump() for d in data])


@router.get("/history")
async def get_briefing_history(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """
    과거 브리핑 목록을 페이지네이션으로 반환합니다.

    Args:
        page: 페이지 번호 (1부터 시작)
        size: 페이지당 항목 수 (최대 100)

    Returns:
        dict: success/data/error 포맷의 브리핑 히스토리
    """
    offset = (page - 1) * size

    count_stmt = select(func.count()).select_from(Briefing)
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()

    stmt = (
        select(Briefing)
        .options(selectinload(Briefing.articles))
        .order_by(Briefing.scheduled_date.desc(), Briefing.period)
        .offset(offset)
        .limit(size)
    )
    result = await db.execute(stmt)
    briefings = result.scalars().all()
    logger.info("Fetched briefing history: page=%d, size=%d, total=%d", page, size, total)

    items = [BriefingResponse.model_validate(b).model_dump() for b in briefings]
    return _success({"items": items, "total": total, "page": page, "size": size})


@router.get("/{period}")
async def get_briefing_by_period(
    period: str,
    target_date: date = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """
    특정 기간(morning/lunch/evening)의 브리핑 상세 정보를 반환합니다.

    Args:
        period: 브리핑 기간 ('morning', 'lunch', 'evening')
        target_date: 조회할 날짜 (기본값: 오늘)

    Returns:
        dict: success/data/error 포맷의 브리핑 상세 정보
    """
    if period not in VALID_PERIODS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid period. Must be one of: {', '.join(VALID_PERIODS)}",
        )

    query_date = target_date or date.today()
    stmt = (
        select(Briefing)
        .where(Briefing.period == period, Briefing.scheduled_date == query_date)
        .options(selectinload(Briefing.articles))
    )
    result = await db.execute(stmt)
    briefing = result.scalar_one_or_none()

    if briefing is None:
        logger.warning("Briefing not found: period=%s, date=%s", period, query_date)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No briefing found for period='{period}' on {query_date}.",
        )

    logger.info("Fetched briefing: id=%s, period=%s, date=%s", briefing.id, period, query_date)
    return _success(BriefingResponse.model_validate(briefing).model_dump())
