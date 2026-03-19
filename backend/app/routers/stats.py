"""
청취 통계 API 라우터.
사용자의 브리핑 청취 통계를 제공합니다.
"""

import logging
from datetime import date, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.listen_history import ListenHistory
from app.utils.auth import get_current_user
from app.utils.response import success_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/stats", tags=["stats"])


@router.get("/listening")
async def get_listening_stats(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """사용자의 전체 청취 통계를 반환합니다."""
    result = await db.execute(
        select(
            func.count(ListenHistory.id),
            func.sum(ListenHistory.listened_seconds),
            func.count(ListenHistory.id).filter(ListenHistory.completed.is_(True)),
        ).where(ListenHistory.user_id == user_id)
    )
    total_count, total_seconds, completed_count = result.one()

    # 연속 청취일 계산: 오늘부터 역순으로 날짜별 청취 기록 확인
    dates_result = await db.execute(
        select(func.date(ListenHistory.listened_at))
        .where(ListenHistory.user_id == user_id)
        .group_by(func.date(ListenHistory.listened_at))
        .order_by(func.date(ListenHistory.listened_at).desc())
    )
    listened_dates = {row[0] for row in dates_result.all()}

    streak_days = 0
    check_date = date.today()
    while check_date in listened_dates:
        streak_days += 1
        check_date -= timedelta(days=1)

    return success_response({
        "total_briefings": total_count or 0,
        "total_minutes": round((total_seconds or 0) / 60, 1),
        "completed_briefings": completed_count or 0,
        "streak_days": streak_days,
    })


@router.get("/listening/weekly")
async def get_weekly_stats(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """최근 7일 간 일별 청취 통계를 반환합니다."""
    today = date.today()
    week_ago = today - timedelta(days=6)

    result = await db.execute(
        select(
            func.date(ListenHistory.listened_at).label("listen_date"),
            func.count(ListenHistory.id).label("count"),
            func.sum(ListenHistory.listened_seconds).label("total_seconds"),
        )
        .where(
            ListenHistory.user_id == user_id,
            func.date(ListenHistory.listened_at) >= week_ago,
        )
        .group_by(func.date(ListenHistory.listened_at))
        .order_by(func.date(ListenHistory.listened_at))
    )
    rows = result.all()

    # 7일 전체를 채워서 반환
    daily_map = {str(row.listen_date): {"count": row.count, "minutes": round(row.total_seconds / 60, 1)} for row in rows}
    weekly = []
    for i in range(7):
        d = str(week_ago + timedelta(days=i))
        weekly.append({
            "date": d,
            "count": daily_map.get(d, {}).get("count", 0),
            "minutes": daily_map.get(d, {}).get("minutes", 0.0),
        })

    return success_response({"weekly": weekly})
