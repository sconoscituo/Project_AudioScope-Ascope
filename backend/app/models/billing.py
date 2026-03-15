"""
BillingUsage 데이터베이스 모델.
Gemini / Supertone API 사용량을 날짜별로 누적 기록합니다.
"""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class BillingUsage(Base):
    """API 비용 사용량 모델."""

    __tablename__ = "billing_usages"
    __table_args__ = (
        Index("ix_billing_service_date", "service", "usage_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    service: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    usage_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    amount_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    request_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    metadata_json: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<BillingUsage service={self.service} date={self.usage_date} "
            f"amount=${self.amount_usd:.4f}>"
        )
