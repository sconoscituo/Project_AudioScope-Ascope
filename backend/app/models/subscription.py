"""
Subscription 데이터베이스 모델.
프리미엄 구독(아침 무료 / 추가 브리핑 유료) 정보를 관리합니다.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Subscription(Base):
    """사용자 구독 모델."""

    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    plan: Mapped[str] = mapped_column(
        String(20), nullable=False, default="free"
    )  # free / monthly / yearly / trial
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )  # active / expired / cancelled
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    payment_provider: Mapped[str | None] = mapped_column(
        String(30), nullable=True
    )  # google_play / app_store / null(free)
    payment_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    price_krw: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="subscription")

    @property
    def is_active_premium(self) -> bool:
        """프리미엄이 활성 상태인지 확인합니다."""
        if self.plan == "free":
            return False
        if self.status != "active":
            return False
        if self.expires_at and self.expires_at < datetime.now(timezone.utc):
            return False
        return True

    def __repr__(self) -> str:
        return f"<Subscription user={self.user_id} plan={self.plan} status={self.status}>"


from app.models.user import User  # noqa: E402
