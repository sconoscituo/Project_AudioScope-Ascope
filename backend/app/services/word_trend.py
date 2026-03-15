"""
주간 뉴스 키워드 트렌드 분석 서비스.
형태소 분석(Okt)으로 명사를 추출하고 빈도를 집계합니다.
KoNLPy 미설치 환경에서는 간단한 정규식 폴백을 사용합니다.
"""

import logging
import re
from collections import Counter
from datetime import date, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.word_trend import WordTrend

logger = logging.getLogger(__name__)

# 불용어 (stopwords)
STOPWORDS = {
    "것", "수", "등", "이", "더", "및", "위", "중", "후", "전", "그",
    "또", "한", "일", "때", "말", "대", "점", "바", "해", "이번",
    "관련", "대한", "통해", "올해", "지난", "최근", "현재", "오늘",
    "내년", "기자", "뉴스", "속보", "사진", "영상", "제공", "연합뉴스",
}

# KoNLPy Okt 초기화 (optional dependency)
_okt = None


def _get_okt():
    """KoNLPy Okt를 lazy 초기화합니다."""
    global _okt
    if _okt is None:
        try:
            from konlpy.tag import Okt
            _okt = Okt()
            logger.info("KoNLPy Okt initialized.")
        except ImportError:
            logger.warning("KoNLPy not available. Using regex fallback for word extraction.")
    return _okt


def extract_nouns(text: str) -> list[str]:
    """텍스트에서 명사를 추출합니다."""
    okt = _get_okt()
    if okt:
        try:
            nouns = okt.nouns(text)
            return [n for n in nouns if len(n) >= 2 and n not in STOPWORDS]
        except Exception as exc:
            logger.warning("Okt extraction failed: %s", exc)

    # Regex 폴백: 한글 2글자 이상 단어 추출
    words = re.findall(r"[가-힣]{2,}", text)
    return [w for w in words if w not in STOPWORDS and len(w) >= 2]


def analyze_articles(articles: list[dict]) -> Counter:
    """기사 목록에서 키워드 빈도를 분석합니다."""
    counter: Counter = Counter()
    for article in articles:
        text = f"{article.get('title', '')} {article.get('description', '')}"
        nouns = extract_nouns(text)
        counter.update(nouns)
    return counter


async def save_weekly_trends(
    db: AsyncSession,
    articles: list[dict],
    week_start: date | None = None,
) -> list[WordTrend]:
    """주간 키워드 트렌드를 DB에 저장합니다."""
    if week_start is None:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    counter = analyze_articles(articles)
    top_words = counter.most_common(50)

    if not top_words:
        return []

    # 기존 해당 주 데이터 삭제 후 재생성 (멱등성)
    await db.execute(
        delete(WordTrend).where(WordTrend.week_start == week_start)
    )

    trends = []
    for word, count in top_words:
        trend = WordTrend(
            word=word,
            count=count,
            week_start=week_start,
            week_end=week_end,
        )
        db.add(trend)
        trends.append(trend)

    await db.flush()
    logger.info("Saved %d word trends for week %s", len(trends), week_start)
    return trends


async def get_weekly_trends(
    db: AsyncSession,
    week_start: date | None = None,
    limit: int = 30,
) -> list[WordTrend]:
    """주간 키워드 트렌드를 조회합니다."""
    if week_start is None:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

    stmt = (
        select(WordTrend)
        .where(WordTrend.week_start == week_start)
        .order_by(WordTrend.count.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
