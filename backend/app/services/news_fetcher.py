"""
뉴스 수집 서비스 모듈.
네이버 검색 API와 RSS 피드를 통해 카테고리별 최신 뉴스를 수집합니다.
"""

import logging
from datetime import datetime
from urllib.parse import quote

import feedparser
import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

NAVER_NEWS_API_URL = "https://openapi.naver.com/v1/search/news.json"

# 브리핑 카테고리별 기본 쿼리
BRIEFING_QUERIES: dict[str, list[str]] = {
    "morning": ["AI 인공지능", "IT 기술", "경제 시장"],
    "lunch":   ["정치 사회", "국제 뉴스", "스타트업"],
    "evening": ["주식 코스피", "문화 엔터테인먼트", "과학 기술"],
}


class NaverNewsFetcher:
    """네이버 검색 API 및 RSS를 통한 뉴스 수집 클라이언트."""

    def __init__(self) -> None:
        """NaverNewsFetcher 초기화."""
        self._headers = {
            "X-Naver-Client-Id": settings.NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": settings.NAVER_CLIENT_SECRET,
        }
        logger.info("NaverNewsFetcher initialized.")

    async def fetch_news(self, query: str, display: int = 10) -> list[dict]:
        """
        네이버 검색 API로 뉴스 기사를 가져옵니다.

        Args:
            query: 검색 쿼리 문자열
            display: 가져올 기사 수 (최대 100)

        Returns:
            list[dict]: 기사 목록 (title, link, description, pubDate, source 포함)
        """
        params = {
            "query": query,
            "display": display,
            "sort": "date",
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    NAVER_NEWS_API_URL, params=params, headers=self._headers
                )
                response.raise_for_status()
            data = response.json()
            items = data.get("items", [])
            logger.info("Fetched %d articles for query '%s'", len(items), query)
            return [self._normalize_naver_item(item) for item in items]
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Naver API HTTP error for query '%s': %s", query, exc, exc_info=True
            )
            return []
        except Exception as exc:
            logger.error(
                "Unexpected error fetching news for query '%s': %s", query, exc, exc_info=True
            )
            return []

    async def fetch_rss(self, url: str) -> list[dict]:
        """
        RSS 피드 URL에서 기사를 파싱하여 반환합니다.

        Args:
            url: RSS 피드 URL

        Returns:
            list[dict]: 기사 목록 (title, link, summary, published, source 포함)
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
            feed = feedparser.parse(response.text)
            articles = [self._normalize_rss_entry(entry) for entry in feed.entries]
            logger.info("Fetched %d articles from RSS: %s", len(articles), url)
            return articles
        except Exception as exc:
            logger.error("RSS fetch error for %s: %s", url, exc, exc_info=True)
            return []

    async def fetch_briefing_articles(self, period: str) -> list[dict]:
        """
        브리핑 기간(morning/lunch/evening)에 맞는 뉴스를 수집합니다.

        Args:
            period: 브리핑 기간 문자열 ('morning', 'lunch', 'evening')

        Returns:
            list[dict]: 중복 제거된 통합 기사 목록
        """
        queries = BRIEFING_QUERIES.get(period, BRIEFING_QUERIES["morning"])
        all_articles: list[dict] = []
        for query in queries:
            articles = await self.fetch_news(query, display=5)
            all_articles.extend(articles)

        # URL 기준 중복 제거
        seen: set[str] = set()
        unique: list[dict] = []
        for article in all_articles:
            url = article.get("link", "")
            if url and url not in seen:
                seen.add(url)
                unique.append(article)

        logger.info(
            "Total unique articles for period '%s': %d", period, len(unique)
        )
        return unique

    @staticmethod
    def _normalize_naver_item(item: dict) -> dict:
        """네이버 API 응답 항목을 공통 포맷으로 변환합니다."""
        import re
        title = re.sub(r"<[^>]+>", "", item.get("title", ""))
        description = re.sub(r"<[^>]+>", "", item.get("description", ""))
        return {
            "title": title,
            "link": item.get("originallink") or item.get("link", ""),
            "description": description,
            "source": item.get("link", "").split("/")[2] if item.get("link") else "",
            "published_at": item.get("pubDate"),
        }

    @staticmethod
    def _normalize_rss_entry(entry: feedparser.FeedParserDict) -> dict:
        """RSS feedparser 항목을 공통 포맷으로 변환합니다."""
        published_at = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                published_at = datetime(*entry.published_parsed[:6]).isoformat()
            except Exception:
                pass
        return {
            "title": getattr(entry, "title", ""),
            "link": getattr(entry, "link", ""),
            "description": getattr(entry, "summary", ""),
            "source": getattr(entry, "source", {}).get("value", ""),
            "published_at": published_at,
        }
