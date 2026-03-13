"""
사용자 관련 Pydantic 스키마 정의.
Firebase Auth 토큰 검증 후 사용자 생성/조회에 사용됩니다.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


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
    created_at: datetime
    last_login_at: datetime | None = None
