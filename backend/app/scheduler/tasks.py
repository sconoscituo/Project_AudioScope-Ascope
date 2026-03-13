"""
APScheduler 기반 브리핑 생성 스케줄러 모듈.
매일 06:00 / 12:00 / 18:00 KST에 브리핑을 자동 생성합니다.
"""

import logging
from datetime import date, datetime, timezone

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.briefing import Briefing
from app.services.billing_monitor import (
    check_daily_gemini_usage,
    check_monthly_supertone_usage,
)
from app.services.news_fetcher import NaverNewsFetcher
from app.services.storage import R2Storage
from app.services.summarizer import GeminiSummarizer
from app.services.tts import SupertoneTTS

logger = logging.getLogger(__name__)

KST = pytz.timezone("Asia/Seoul")

scheduler = AsyncIOScheduler(timezone=KST)


def setup_scheduler() -> AsyncIOScheduler:
    """
    스케줄러에 브리핑 생성 작업을 등록하고 반환합니다.

    Returns:
        AsyncIOScheduler: 작업이 등록된 스케줄러 인스턴스
    """
    scheduler.add_job(
        generate_morning_briefing,
        trigger=CronTrigger(hour=6, minute=0, timezone=KST),
        id="morning_briefing",
        replace_existing=True,
        misfire_grace_time=300,
    )
    scheduler.add_job(
        generate_lunch_briefing,
        trigger=CronTrigger(hour=12, minute=0, timezone=KST),
        id="lunch_briefing",
        replace_existing=True,
        misfire_grace_time=300,
    )
    scheduler.add_job(
        generate_evening_briefing,
        trigger=CronTrigger(hour=18, minute=0, timezone=KST),
        id="evening_briefing",
        replace_existing=True,
        misfire_grace_time=300,
    )
    logger.info("Scheduler jobs registered: morning(06:00), lunch(12:00), evening(18:00) KST")
    return scheduler


async def generate_morning_briefing() -> None:
    """06:00 KST 아침 브리핑 생성 작업."""
    await generate_briefing("morning")


async def generate_lunch_briefing() -> None:
    """12:00 KST 점심 브리핑 생성 작업."""
    await generate_briefing("lunch")


async def generate_evening_briefing() -> None:
    """18:00 KST 저녁 브리핑 생성 작업."""
    await generate_briefing("evening")


async def generate_briefing(period: str) -> None:
    """
    브리핑 생성 파이프라인을 실행합니다.
    뉴스 수집 → AI 요약 → TTS 변환 → R2 업로드 → DB 저장

    Args:
        period: 브리핑 기간 ('morning', 'lunch', 'evening')
    """
    today = date.today()
    logger.info("Starting briefing generation: period=%s, date=%s", period, today)

    async with AsyncSessionLocal() as db:
        # 이미 completed 상태인 브리핑이 있으면 스킵
        stmt = select(Briefing).where(
            Briefing.period == period,
            Briefing.scheduled_date == today,
            Briefing.status == "completed",
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            logger.info(
                "Briefing already completed for period=%s, date=%s. Skipping.",
                period, today,
            )
            return

        # DB에 pending 레코드 생성
        briefing = Briefing(
            period=period,
            scheduled_date=today,
            status="generating",
        )
        db.add(briefing)
        await db.flush()
        briefing_id = briefing.id
        logger.info("Briefing record created: id=%s", briefing_id)

        try:
            # 1. 뉴스 수집
            fetcher = NaverNewsFetcher()
            articles = await fetcher.fetch_briefing_articles(period)
            if not articles:
                raise RuntimeError("No articles fetched for period: " + period)

            # 2. AI 요약
            summarizer = GeminiSummarizer()
            script = await summarizer.summarize_articles(articles, period, db)

            # 3. TTS 변환
            tts = SupertoneTTS()
            audio_bytes = await tts.text_to_speech(script, db)

            # 4. R2 업로드
            storage = R2Storage()
            object_key = R2Storage.generate_object_key(period, today.isoformat())
            audio_url = await storage.upload_audio(audio_bytes, object_key)

            # 5. DB 업데이트
            briefing.audio_url = audio_url
            briefing.status = "completed"
            briefing.article_count = len(articles)
            briefing.generated_at = datetime.now(timezone.utc)
            await db.commit()

            logger.info(
                "Briefing generation complete: id=%s, period=%s, articles=%d, url=%s",
                briefing_id, period, len(articles), audio_url,
            )

            # 6. 빌링 체크
            await check_daily_gemini_usage(db)
            await check_monthly_supertone_usage(db)

        except Exception as exc:
            briefing.status = "failed"
            await db.commit()
            logger.error(
                "Briefing generation failed: id=%s, period=%s, error=%s",
                briefing_id, period, exc, exc_info=True,
            )
