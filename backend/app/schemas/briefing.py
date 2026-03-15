"""
브리핑 관련 Pydantic 스키마 정의.
API 요청/응답 직렬화에 사용됩니다.
"""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class ArticleResponse(BaseModel):
    """개별 기사 응답 스키마."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    original_url: str
    summary: str | None = None
    full_content: str | None = None
    category: str | None = None
    source: str | None = None
    thumbnail_url: str | None = None
    video_url: str | None = None
    display_order: int = 0
    published_at: datetime | None = None


class BriefingResponse(BaseModel):
    """단일 브리핑 응답 스키마."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    period: str
    scheduled_date: date
    title: str | None = None
    audio_url: str | None = None
    audio_duration_seconds: int | None = None
    status: str
    article_count: int
    generated_at: datetime | None = None
    created_at: datetime
    articles: list[ArticleResponse] = []
    is_listened: bool = False
    is_free: bool = False


class BriefingListItem(BaseModel):
    """브리핑 목록 아이템 (articles 미포함)."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    period: str
    scheduled_date: date
    title: str | None = None
    audio_url: str | None = None
    audio_duration_seconds: int | None = None
    status: str
    article_count: int
    generated_at: datetime | None = None
    is_listened: bool = False
    is_free: bool = False


class ListenProgressRequest(BaseModel):
    """청취 진행도 업데이트 요청."""
    briefing_id: uuid.UUID
    listened_seconds: int
    completed: bool = False
