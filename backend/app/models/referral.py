"""
Referral 데이터베이스 모델.
추천인 보상 시스템: 3명 추천 시 프리미엄 기능 잠금해제.
(Morning Brew 검증 모델 적용)
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Referral(Base):
    """추천 기록 모델."""

    __tablename__ = "referrals"
    __table_args__ = (
        UniqueConstraint("referrer_id", "referred_id", name="uq_referral"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    referrer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    referred_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    referral_code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    reward_granted: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Referral referrer={self.referrer_id} referred={self.referred_id}>"
