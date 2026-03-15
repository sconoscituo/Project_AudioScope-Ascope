"""
트렌드 API 라우터.
주간 뉴스 키워드 트렌드를 제공합니다.
"""

import logging
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.trend import WeeklyTrendResponse, WordTrendItem
from app.services.word_trend import get_weekly_trends
from app.utils.auth import get_current_user
from app.utils.response import success_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/trends", tags=["trends"])


@router.get("/weekly")
async def get_weekly_word_trends(
    week_offset: int = Query(default=0, ge=0, le=12, description="0=이번주, 1=지난주..."),
    limit: int = Query(default=30, ge=5, le=50),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    """금주(또는 지정 주) 뉴스에서 가장 많이 나온 키워드를 반환합니다."""
    today = date.today()
    target_start = today - timedelta(days=today.weekday() + 7 * week_offset)

    trends = await get_weekly_trends(db, target_start, limit)

    words = [
        WordTrendItem(word=t.word, count=t.count, category=t.category)
        for t in trends
    ]

    return success_response(
        WeeklyTrendResponse(
            week_start=target_start,
            week_end=target_start + timedelta(days=6),
            words=words,
            total_articles_analyzed=sum(w.count for w in words),
        ).model_dump()
    )
