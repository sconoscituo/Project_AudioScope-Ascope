"""
ListenHistory 데이터베이스 모델.
사용자가 청취한 브리핑을 기록하여 중복 청취를 방지합니다.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ListenHistory(Base):
    """사용자 청취 기록 모델."""

    __tablename__ = "listen_history"
    __table_args__ = (
        UniqueConstraint("user_id", "briefing_id", name="uq_user_briefing_listen"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    briefing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("briefings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    listened_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed: Mapped[bool] = mapped_column(default=False, nullable=False)
    listened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="listen_history")
    briefing: Mapped["Briefing"] = relationship("Briefing")

    def __repr__(self) -> str:
        return f"<ListenHistory user={self.user_id} briefing={self.briefing_id}>"


from app.models.briefing import Briefing  # noqa: E402
from app.models.user import User  # noqa: E402
