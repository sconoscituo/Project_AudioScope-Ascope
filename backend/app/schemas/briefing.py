"""
브리핑 관련 Pydantic 스키마 정의.
API 요청/응답 직렬화에 사용됩니다.
"""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, HttpUrl


class ArticleSummary(BaseModel):
    """개별 기사 요약 스키마."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    original_url: str
    summary: str | None = None
    source: str | None = None
    published_at: datetime | None = None


class BriefingResponse(BaseModel):
    """단일 브리핑 응답 스키마."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    period: str
    scheduled_date: date
    audio_url: str | None = None
    status: str
    article_count: int
    generated_at: datetime | None = None
    created_at: datetime
    articles: list[ArticleSummary] = []


class BriefingListResponse(BaseModel):
    """브리핑 목록 응답 스키마."""

    model_config = ConfigDict(from_attributes=True)

    items: list[BriefingResponse]
    total: int
    page: int = 1
    size: int = 20
