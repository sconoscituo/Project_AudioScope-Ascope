"""
트렌드 관련 Pydantic 스키마.
"""

from datetime import date

from pydantic import BaseModel


class WordTrendItem(BaseModel):
    """단일 키워드 트렌드."""
    word: str
    count: int
    category: str | None = None


class WeeklyTrendResponse(BaseModel):
    """주간 키워드 트렌드 응답."""
    week_start: date
    week_end: date
    words: list[WordTrendItem]
    total_articles_analyzed: int = 0
