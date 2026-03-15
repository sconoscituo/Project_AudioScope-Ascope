"""
구독 관련 Pydantic 스키마.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SubscriptionResponse(BaseModel):
    """구독 정보 응답."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    plan: str
    status: str
    started_at: datetime
    expires_at: datetime | None = None
    is_active_premium: bool = False
    price_krw: int = 0


class SubscriptionCreateRequest(BaseModel):
    """구독 생성/업그레이드 요청."""
    plan: str  # monthly / yearly
    payment_provider: str  # google_play / app_store
    payment_id: str
    price_krw: int


class SubscriptionCancelRequest(BaseModel):
    """구독 취소 요청."""
    reason: str | None = None
