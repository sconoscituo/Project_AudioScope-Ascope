"""
브리핑 레포지토리 포트 (인터페이스).
헥사고날 아키텍처에서 도메인 레이어가 인프라에 의존하지 않도록 추상화합니다.
"""

import uuid
from abc import ABCMeta, abstractmethod
from datetime import date

from app.domain.models.briefing import BriefingDomain


class AbstractBriefingRepository(metaclass=ABCMeta):
    """브리핑 CRUD를 위한 추상 레포지토리 인터페이스."""

    @abstractmethod
    async def get_by_id(self, briefing_id: uuid.UUID) -> BriefingDomain | None:
        """ID로 브리핑을 조회합니다."""
        ...

    @abstractmethod
    async def get_by_period_and_date(
        self, period: str, scheduled_date: date
    ) -> BriefingDomain | None:
        """기간(morning/lunch/evening)과 날짜로 브리핑을 조회합니다."""
        ...

    @abstractmethod
    async def list_by_date(self, scheduled_date: date) -> list[BriefingDomain]:
        """특정 날짜의 모든 브리핑을 반환합니다."""
        ...

    @abstractmethod
    async def save(self, briefing: BriefingDomain) -> BriefingDomain:
        """브리핑을 저장(생성 또는 업데이트)합니다."""
        ...

    @abstractmethod
    async def delete(self, briefing_id: uuid.UUID) -> bool:
        """브리핑을 삭제합니다. 성공 여부를 반환합니다."""
        ...
