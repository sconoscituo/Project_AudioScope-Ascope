"""
Briefing 및 BriefingArticle 데이터베이스 모델.
스케줄러가 생성한 오디오 브리핑과 원본 기사 정보를 저장합니다.
"""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Briefing(Base):
    """오디오 브리핑 모델 (morning/lunch/evening)."""

    __tablename__ = "briefings"
    __table_args__ = (
        UniqueConstraint("period", "scheduled_date", name="uq_briefing_period_date"),
        Index("ix_briefing_date_period", "scheduled_date", "period"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    period: Mapped[str] = mapped_column(String(10), nullable=False)
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    script: Mapped[str | None] = mapped_column(Text, nullable=True)
    audio_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    audio_duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )
    article_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    generated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    generation_cost_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    articles: Mapped[list["BriefingArticle"]] = relationship(
        "BriefingArticle", back_populates="briefing", cascade="all, delete-orphan",
        order_by="BriefingArticle.display_order",
    )

    def __repr__(self) -> str:
        return f"<Briefing id={self.id} period={self.period} date={self.scheduled_date} status={self.status}>"


class BriefingArticle(Base):
    """브리핑에 포함된 개별 기사 모델."""

    __tablename__ = "briefing_articles"
    __table_args__ = (
        Index("ix_article_briefing_order", "briefing_id", "display_order"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    briefing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("briefings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    original_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    full_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    video_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    briefing: Mapped["Briefing"] = relationship("Briefing", back_populates="articles")

    def __repr__(self) -> str:
        return f"<BriefingArticle id={self.id} title={self.title[:40]}>"
