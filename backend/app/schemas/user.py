"""
사용자 관련 Pydantic 스키마 정의.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    """사용자 생성 요청 스키마 (Firebase ID 토큰 필요)."""
    firebase_token: str


class UserResponse(BaseModel):
    """사용자 정보 응답 스키마."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    firebase_uid: str
    email: str | None = None
    display_name: str | None = None
    provider: str
    is_active: bool
    is_premium: bool
    profile_image_url: str | None = None
    total_listen_count: int = 0
    total_listen_seconds: int = 0
    created_at: datetime
    last_login_at: datetime | None = None
    categories: list[str] = []


class UserUpdateRequest(BaseModel):
    """사용자 정보 수정 요청."""
    display_name: str | None = None
    fcm_token: str | None = None


class CategoryUpdateRequest(BaseModel):
    """카테고리 선호도 업데이트 요청."""
    categories: list[str]
