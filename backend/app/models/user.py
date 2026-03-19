"""
User 및 UserCategoryPreference 데이터베이스 모델.
Firebase Auth 사용자 정보 + 뉴스 카테고리 선호도를 저장합니다.
"""

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# 지원하는 뉴스 카테고리 목록
NEWS_CATEGORIES = {
    "politics": "정치",
    "economy": "경제",
    "society": "사회",
    "world": "국제",
    "tech": "IT/기술",
    "science": "과학",
    "culture": "문화",
    "sports": "스포츠",
    "entertainment": "연예",
    "lifestyle": "생활",
}


class User(Base):
    """사용자 모델."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    firebase_uid: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False, index=True
    )
    email: Mapped[str | None] = mapped_column(String(320), unique=True, nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    referral_code: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True, index=True)
    fcm_token: Mapped[str | None] = mapped_column(String(512), nullable=True)
    preferred_voice_id: Mapped[str] = mapped_column(String(64), default="ko-KR-female-1", nullable=False)
    profile_image_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    total_listen_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_listen_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    preferred_categories: Mapped[list | None] = mapped_column(
        JSON, default=lambda: ["tech", "economy", "society"], nullable=True
    )
    briefing_times: Mapped[list | None] = mapped_column(
        JSON, default=lambda: ["morning", "evening"], nullable=True
    )
    notification_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    category_preferences: Mapped[list["UserCategoryPreference"]] = relationship(
        "UserCategoryPreference", back_populates="user", cascade="all, delete-orphan"
    )
    subscription: Mapped["Subscription | None"] = relationship(
        "Subscription", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    listen_history: Mapped[list["ListenHistory"]] = relationship(
        "ListenHistory", back_populates="user", cascade="all, delete-orphan"
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} premium={self.is_premium}>"


class UserCategoryPreference(Base):
    """사용자 뉴스 카테고리 선호도 모델."""

    __tablename__ = "user_category_preferences"
    __table_args__ = (
        UniqueConstraint("user_id", "category", name="uq_user_category"),
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
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="category_preferences")

    def __repr__(self) -> str:
        return f"<UserCategoryPreference user={self.user_id} cat={self.category}>"


# Forward references
from app.models.listen_history import ListenHistory  # noqa: E402
from app.models.refresh_token import RefreshToken  # noqa: E402
from app.models.subscription import Subscription  # noqa: E402
