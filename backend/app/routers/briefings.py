"""
브리핑 API 라우터.
오늘의 브리핑 조회, 기사 상세, 청취 기록 관리를 제공합니다.
프리미엄 접근 권한 검증을 포함합니다.
"""

import logging
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any

KST = timezone(timedelta(hours=9))

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.database import get_db
from app.models.briefing import Briefing, BriefingArticle
from app.models.listen_history import ListenHistory
from app.models.user import User
from app.schemas.briefing import (
    ArticleResponse,
    BriefingListItem,
    BriefingResponse,
    ListenProgressRequest,
)
from app.services.subscription import check_briefing_access
from app.utils.auth import get_current_user
from app.utils.response import error_response, paginated_response, success_response

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/api/v1/briefings", tags=["briefings"])

VALID_PERIODS = {"morning", "lunch", "evening"}


@router.get("/today")
async def get_today_briefings(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """오늘의 브리핑 목록을 반환합니다. 프리미엄 여부에 따라 잠금 표시."""
    today = datetime.now(KST).date()
    stmt = (
        select(Briefing)
        .where(Briefing.scheduled_date == today)
        .options(selectinload(Briefing.articles))
        .order_by(Briefing.period)
    )
    result = await db.execute(stmt)
    briefings = result.scalars().all()

    # 청취 기록 확인
    listen_stmt = select(ListenHistory.briefing_id).where(
        ListenHistory.user_id == user_id,
    )
    listen_result = await db.execute(listen_stmt)
    listened_ids = {row[0] for row in listen_result.all()}

    data = []
    for b in briefings:
        can_access, reason = await check_briefing_access(db, user_id, b.period)
        item = BriefingResponse.model_validate(b)
        item.is_listened = b.id in listened_ids
        item.is_free = b.period == settings.FREE_BRIEFING_PERIOD
        d = item.model_dump()
        d["is_locked"] = not can_access
        d["lock_reason"] = reason if not can_access else None
        data.append(d)

    return success_response(data)


@router.get("/history")
async def get_briefing_history(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """과거 브리핑 목록을 페이지네이션으로 반환합니다."""
    offset = (page - 1) * size

    count_stmt = select(func.count()).select_from(Briefing).where(
        Briefing.status == "completed"
    )
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = (
        select(Briefing)
        .where(Briefing.status == "completed")
        .order_by(Briefing.scheduled_date.desc(), Briefing.period)
        .offset(offset)
        .limit(size)
    )
    result = await db.execute(stmt)
    briefings = result.scalars().all()

    # 청취 기록
    listen_stmt = select(ListenHistory.briefing_id).where(
        ListenHistory.user_id == user_id,
    )
    listened_ids = {row[0] for row in (await db.execute(listen_stmt)).all()}

    items = []
    for b in briefings:
        item = BriefingListItem.model_validate(b)
        item.is_listened = b.id in listened_ids
        item.is_free = b.period == settings.FREE_BRIEFING_PERIOD
        items.append(item.model_dump())

    return paginated_response(items, total, page, size)


@router.get("/unlistened")
async def get_unlistened_briefings(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """사용자가 아직 듣지 않은 최근 브리핑을 반환합니다."""
    listened_subq = (
        select(ListenHistory.briefing_id)
        .where(ListenHistory.user_id == user_id)
        .subquery()
    )
    stmt = (
        select(Briefing)
        .where(
            Briefing.status == "completed",
            Briefing.id.notin_(select(listened_subq)),
        )
        .order_by(Briefing.scheduled_date.desc(), Briefing.period)
        .limit(10)
    )
    result = await db.execute(stmt)
    briefings = result.scalars().all()

    items = [BriefingListItem.model_validate(b).model_dump() for b in briefings]
    return success_response(items)


@router.get("/{period}")
async def get_briefing_by_period(
    period: str,
    target_date: date = Query(default=None),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """특정 기간의 브리핑 상세 정보를 반환합니다."""
    if period not in VALID_PERIODS:
        raise HTTPException(status_code=400, detail=f"Invalid period: {period}")

    # 접근 권한 확인
    can_access, reason = await check_briefing_access(db, user_id, period)
    if not can_access:
        return error_response("프리미엄 구독이 필요합니다.", status_code=403)

    query_date = target_date or date.today()
    stmt = (
        select(Briefing)
        .where(Briefing.period == period, Briefing.scheduled_date == query_date)
        .options(selectinload(Briefing.articles))
    )
    result = await db.execute(stmt)
    briefing = result.scalar_one_or_none()

    if briefing is None:
        raise HTTPException(status_code=404, detail="Briefing not found.")

    return success_response(BriefingResponse.model_validate(briefing).model_dump())


@router.get("/articles/{article_id}")
async def get_article_detail(
    article_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    """개별 기사의 상세 정보를 반환합니다."""
    stmt = select(BriefingArticle).where(BriefingArticle.id == article_id)
    result = await db.execute(stmt)
    article = result.scalar_one_or_none()

    if article is None:
        raise HTTPException(status_code=404, detail="Article not found.")

    return success_response(ArticleResponse.model_validate(article).model_dump())


@router.post("/listen")
async def record_listen_progress(
    body: ListenProgressRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """청취 진행도를 기록합니다 (중복 청취 방지용)."""
    # UPSERT: 이미 있으면 업데이트
    stmt = select(ListenHistory).where(
        ListenHistory.user_id == user_id,
        ListenHistory.briefing_id == body.briefing_id,
    )
    result = await db.execute(stmt)
    history = result.scalar_one_or_none()

    user_stmt = select(User).where(User.id == user_id)
    user = (await db.execute(user_stmt)).scalar_one_or_none()

    if history is None:
        history = ListenHistory(
            user_id=user_id,
            briefing_id=body.briefing_id,
            listened_seconds=body.listened_seconds,
            completed=body.completed,
        )
        db.add(history)

        # 유저 통계 업데이트 (신규 기록)
        if user:
            user.total_listen_count += 1
            user.total_listen_seconds += body.listened_seconds
    else:
        # 기존 기록: delta만큼만 추가
        delta = max(0, body.listened_seconds - history.listened_seconds)
        history.listened_seconds = max(history.listened_seconds, body.listened_seconds)
        history.completed = history.completed or body.completed
        if user:
            user.total_listen_seconds += delta

    await db.flush()
    return success_response({"recorded": True})
