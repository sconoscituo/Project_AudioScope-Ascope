"""
WordTrend 데이터베이스 모델.
주간 뉴스 키워드 빈도 분석 결과를 저장합니다.
"""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class WordTrend(Base):
    """주간 뉴스 키워드 트렌드 모델."""

    __tablename__ = "word_trends"
    __table_args__ = (
        Index("ix_word_trend_week_count", "week_start", "count"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    word: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    category: Mapped[str | None] = mapped_column(String(30), nullable=True)
    week_start: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    week_end: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<WordTrend word={self.word} count={self.count} week={self.week_start}>"
