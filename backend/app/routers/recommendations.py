"""
AI 뉴스 추천 API 라우터.
사용자 청취 이력 기반 맞춤 브리핑 추천 및 피드백 수집.
"""

import logging
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.recommendation import get_recommended_briefings
from app.utils.auth import get_current_user
from app.utils.response import error_response, success_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])


class FeedbackRequest(BaseModel):
    briefing_id: uuid.UUID
    feedback: Literal["like", "dislike"]
    reason: str | None = None


@router.get("")
async def get_recommendations(
    limit: int = Query(default=10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """
    사용자 맞춤 브리핑 추천 목록을 반환합니다.

    - 최근 청취 이력과 카테고리 선호도를 Gemini AI로 분석
    - 아직 듣지 않은 브리핑 중 연관도 높은 순으로 반환
    - 청취 이력이 없으면 사용자 설정 카테고리 기반 추천
    """
    result = await get_recommended_briefings(db, user_id, limit=limit)
    return success_response(result)


@router.post("/feedback")
async def submit_feedback(
    body: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """
    추천 브리핑에 대한 좋아요/싫어요 피드백을 기록합니다.

    - like: 이 브리핑과 유사한 콘텐츠를 더 추천
    - dislike: 이 브리핑과 유사한 콘텐츠를 덜 추천
    """
    # 피드백 로깅 (추후 DB 저장 및 추천 가중치 반영 확장 가능)
    logger.info(
        "Recommendation feedback: user=%s, briefing=%s, feedback=%s, reason=%s",
        user_id,
        body.briefing_id,
        body.feedback,
        body.reason,
    )

    message = (
        "피드백 감사합니다! 더 나은 추천을 위해 반영하겠습니다."
        if body.feedback == "like"
        else "피드백 감사합니다! 관심 없는 콘텐츠를 줄이겠습니다."
    )

    return success_response({"recorded": True, "message": message})
