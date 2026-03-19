"""
즐겨찾기 기사 API 라우터.
사용자가 기사를 즐겨찾기로 저장하고 관리하는 기능을 제공합니다.
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.favorite import FavoriteArticle
from app.utils.auth import get_current_user
from app.utils.response import success_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/favorites", tags=["favorites"])


@router.post("/{article_id}")
async def save_favorite(
    article_id: str,
    title: str = "",
    summary: str = "",
    source: str = "",
    url: str = "",
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """기사를 즐겨찾기로 저장합니다. 이미 저장된 경우 중복 저장하지 않습니다."""
    # 중복 확인
    stmt = select(FavoriteArticle).where(
        FavoriteArticle.user_id == user_id,
        FavoriteArticle.article_id == article_id,
    )
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        return success_response({"message": "이미 즐겨찾기에 저장된 기사입니다."})

    fav = FavoriteArticle(
        user_id=user_id,
        article_id=article_id,
        title=title or None,
        summary=summary or None,
        source=source or None,
        url=url or None,
    )
    db.add(fav)
    await db.flush()
    logger.info("Favorite saved: user=%s, article=%s", user_id, article_id)
    return success_response({"message": "즐겨찾기 저장됨"})


@router.get("/")
async def list_favorites(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """사용자의 즐겨찾기 기사 목록을 반환합니다."""
    stmt = (
        select(FavoriteArticle)
        .where(FavoriteArticle.user_id == user_id)
        .order_by(FavoriteArticle.saved_at.desc())
    )
    result = await db.execute(stmt)
    favs = result.scalars().all()

    data = [
        {
            "id": str(f.id),
            "article_id": f.article_id,
            "title": f.title,
            "summary": f.summary,
            "source": f.source,
            "url": f.url,
            "saved_at": f.saved_at.isoformat() if f.saved_at else None,
        }
        for f in favs
    ]
    return success_response({"favorites": data, "total": len(data)})


@router.delete("/{article_id}")
async def remove_favorite(
    article_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """즐겨찾기에서 기사를 삭제합니다."""
    stmt = select(FavoriteArticle).where(
        FavoriteArticle.article_id == article_id,
        FavoriteArticle.user_id == user_id,
    )
    fav = (await db.execute(stmt)).scalar_one_or_none()
    if fav:
        await db.delete(fav)
        await db.flush()
        logger.info("Favorite removed: user=%s, article=%s", user_id, article_id)
    return success_response({"message": "삭제됨"})
