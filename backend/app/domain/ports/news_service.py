"""
뉴스 서비스 포트 (인터페이스).
뉴스 수집 구현체를 교체 가능하도록 추상화합니다.
"""

from abc import ABCMeta, abstractmethod


class AbstractNewsService(metaclass=ABCMeta):
    """뉴스 수집을 위한 추상 서비스 인터페이스."""

    @abstractmethod
    async def fetch_briefing_articles(
        self,
        period: str,
        user_categories: list[str] | None = None,
    ) -> list[dict]:
        """
        브리핑 기간에 맞는 뉴스 기사를 수집합니다.

        Args:
            period: 브리핑 시간대 ('morning', 'lunch', 'evening')
            user_categories: 사용자 선호 카테고리 목록 (None이면 기본값 사용)

        Returns:
            수집된 기사 dict 목록
        """
        ...

    @abstractmethod
    async def fetch_by_categories(
        self,
        categories: list[str],
        articles_per_category: int = 5,
    ) -> list[dict]:
        """
        카테고리 목록으로 뉴스를 수집합니다.

        Args:
            categories: 수집할 카테고리 목록
            articles_per_category: 카테고리당 최대 기사 수

        Returns:
            수집된 기사 dict 목록
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """HTTP 클라이언트 등 리소스를 정리합니다."""
        ...
