"""
뉴스 수집 서비스 모듈.
네이버 검색 API와 RSS를 통해 카테고리별 최신 뉴스를 수집합니다.
썸네일, 카테고리 분류, 중복 제거를 포함합니다.
"""

import asyncio
import logging
import re
from datetime import datetime

import httpx
from bs4 import BeautifulSoup

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

NAVER_NEWS_API_URL = "https://openapi.naver.com/v1/search/news.json"

# 카테고리별 검색 쿼리 매핑
CATEGORY_QUERIES: dict[str, list[str]] = {
    "politics": ["정치 국회", "대통령 정책"],
    "economy": ["경제 시장", "금리 물가", "주식 코스피"],
    "society": ["사회 이슈", "교육 복지"],
    "world": ["국제 뉴스", "세계 외교"],
    "tech": ["AI 인공지능", "IT 기술 스타트업"],
    "science": ["과학 연구", "우주 기술"],
    "culture": ["문화 예술", "도서 전시"],
    "sports": ["스포츠 축구", "야구 NBA"],
    "entertainment": ["연예 드라마", "K-POP 아이돌"],
    "lifestyle": ["건강 생활", "여행 맛집"],
}

# 시간대별 기본 카테고리
PERIOD_DEFAULT_CATEGORIES: dict[str, list[str]] = {
    "morning": ["politics", "economy", "world", "tech"],
    "lunch": ["society", "science", "culture", "lifestyle"],
    "evening": ["economy", "world", "tech", "sports"],
}


class NaverNewsFetcher:
    """네이버 검색 API 및 RSS를 통한 뉴스 수집 클라이언트."""

    def __init__(self) -> None:
        self._headers = {
            "X-Naver-Client-Id": settings.NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": settings.NAVER_CLIENT_SECRET,
        }
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """재사용 가능한 HTTP 클라이언트를 반환합니다 (커넥션 풀링)."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(15.0, connect=5.0),
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def fetch_news(self, query: str, display: int = 10) -> list[dict]:
        """네이버 검색 API로 뉴스 기사를 가져옵니다."""
        params = {"query": query, "display": min(display, 100), "sort": "date"}
        try:
            client = await self._get_client()
            response = await client.get(
                NAVER_NEWS_API_URL, params=params, headers=self._headers
            )
            response.raise_for_status()
            data = response.json()
            items = data.get("items", [])
            logger.info("Fetched %d articles for query '%s'", len(items), query)
            return [self._normalize_naver_item(item) for item in items]
        except httpx.HTTPStatusError as exc:
            logger.error("Naver API HTTP error for '%s': %s", query, exc.response.status_code)
            return []
        except Exception as exc:
            logger.error("Unexpected error fetching '%s': %s", query, exc)
            return []

    async def fetch_by_categories(
        self,
        categories: list[str],
        articles_per_category: int = 5,
    ) -> list[dict]:
        """
        여러 카테고리의 뉴스를 동시 수집합니다 (asyncio.gather 병렬 처리).
        """
        tasks = []
        for category in categories:
            queries = CATEGORY_QUERIES.get(category, [])
            for query in queries[:2]:
                tasks.append(self._fetch_with_category(query, category, articles_per_category))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        all_articles: list[dict] = []
        for result in results:
            if isinstance(result, list):
                all_articles.extend(result)
            elif isinstance(result, Exception):
                logger.error("Category fetch error: %s", result)

        unique = self._deduplicate(all_articles)
        logger.info("Total unique articles across %d categories: %d", len(categories), len(unique))
        return unique

    async def _fetch_with_category(
        self, query: str, category: str, display: int
    ) -> list[dict]:
        """카테고리 태그를 붙여 뉴스를 가져옵니다."""
        articles = await self.fetch_news(query, display)
        for article in articles:
            article["category"] = category
        return articles

    async def fetch_briefing_articles(
        self,
        period: str,
        user_categories: list[str] | None = None,
    ) -> list[dict]:
        """
        브리핑 기간에 맞는 뉴스를 수집합니다.
        사용자 카테고리 선호도를 반영합니다.
        """
        if user_categories:
            categories = user_categories
        else:
            categories = PERIOD_DEFAULT_CATEGORIES.get(
                period, PERIOD_DEFAULT_CATEGORIES["morning"]
            )

        articles = await self.fetch_by_categories(categories, articles_per_category=4)

        # 썸네일 추출 (병렬)
        articles_with_thumbnails = await self._enrich_thumbnails(articles[:settings.MAX_ARTICLES_PER_BRIEFING])

        return articles_with_thumbnails

    async def _enrich_thumbnails(self, articles: list[dict]) -> list[dict]:
        """기사 URL에서 OG 이미지(썸네일)를 추출합니다."""
        tasks = [self._extract_og_image(a.get("link", "")) for a in articles]
        thumbnails = await asyncio.gather(*tasks, return_exceptions=True)
        for article, thumb in zip(articles, thumbnails):
            if isinstance(thumb, str) and thumb:
                article["thumbnail_url"] = thumb
        return articles

    async def _extract_og_image(self, url: str) -> str | None:
        """URL의 og:image 메타태그에서 썸네일 URL을 추출합니다."""
        if not url:
            return None
        try:
            client = await self._get_client()
            response = await client.get(url, follow_redirects=True, timeout=5.0)
            if response.status_code != 200:
                return None
            soup = BeautifulSoup(response.text[:10000], "html.parser")
            og_image = soup.find("meta", property="og:image")
            if og_image and og_image.get("content"):
                return str(og_image["content"])
            # video도 찾기
            og_video = soup.find("meta", property="og:video")
            if og_video and og_video.get("content"):
                return None  # video_url은 별도 처리
            return None
        except Exception:
            return None

    @staticmethod
    def _normalize_naver_item(item: dict) -> dict:
        """네이버 API 응답 항목을 공통 포맷으로 변환합니다."""
        title = re.sub(r"<[^>]+>", "", item.get("title", ""))
        description = re.sub(r"<[^>]+>", "", item.get("description", ""))
        link = item.get("originallink") or item.get("link", "")
        source = ""
        if item.get("link"):
            parts = item["link"].split("/")
            if len(parts) > 2:
                source = parts[2]
        return {
            "title": title.strip(),
            "link": link,
            "description": description.strip(),
            "source": source,
            "published_at": item.get("pubDate"),
            "thumbnail_url": None,
            "video_url": None,
            "category": None,
        }

    @staticmethod
    def _deduplicate(articles: list[dict]) -> list[dict]:
        """URL 기준으로 중복을 제거합니다."""
        seen: set[str] = set()
        unique: list[dict] = []
        for article in articles:
            url = article.get("link", "")
            title = article.get("title", "")
            key = url or title
            if key and key not in seen:
                seen.add(key)
                unique.append(article)
        return unique
