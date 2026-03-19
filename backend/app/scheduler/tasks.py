"""
APScheduler 기반 브리핑 생성 스케줄러.
매일 06:00/12:00/18:00 KST에 브리핑을 자동 생성합니다.
키워드 트렌드 분석, 구독 만료 처리도 수행합니다.
"""

import logging
from datetime import date, datetime, timezone

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from app.config import get_settings as _get_settings
from app.database import get_db_context
from app.models.briefing import Briefing, BriefingArticle
from app.models.user import User
from app.services.billing_monitor import (
    check_daily_gemini_usage,
    check_monthly_supertone_usage,
    send_slack_alert,
)
from app.services.news_fetcher import NaverNewsFetcher
from app.services.push_notification import FCMService
from app.services.storage import SupabaseStorage
from app.services.subscription import check_expired_subscriptions
from app.services.summarizer import GeminiSummarizer
from app.services.tts import SupertoneTTS
from app.services.word_trend import save_weekly_trends

logger = logging.getLogger(__name__)
KST = pytz.timezone("Asia/Seoul")

scheduler = AsyncIOScheduler(timezone=KST)


def setup_scheduler() -> AsyncIOScheduler:
    """스케줄러에 작업을 등록합니다."""
    # 브리핑 생성 (06:00, 12:00, 18:00 KST)
    for hour, period in [(6, "morning"), (12, "lunch"), (18, "evening")]:
        scheduler.add_job(
            _generate_briefing_wrapper,
            trigger=CronTrigger(hour=hour, minute=0, timezone=KST),
            args=[period],
            id=f"{period}_briefing",
            replace_existing=True,
            misfire_grace_time=600,
        )

    # 구독 만료 처리 (매일 자정 KST)
    scheduler.add_job(
        _check_expired_subscriptions,
        trigger=CronTrigger(hour=0, minute=5, timezone=KST),
        id="check_expired_subs",
        replace_existing=True,
    )

    # 주간 키워드 트렌드 갱신 (매일 19:00 KST, 저녁 브리핑 이후)
    scheduler.add_job(
        _update_weekly_trends,
        trigger=CronTrigger(hour=19, minute=0, timezone=KST),
        id="weekly_trends",
        replace_existing=True,
    )

    logger.info("Scheduler jobs registered: morning(06), lunch(12), evening(18) KST + maintenance")
    return scheduler


async def _generate_briefing_wrapper(period: str) -> None:
    """에러 발생 시에도 스케줄러가 멈추지 않도록 래핑합니다."""
    try:
        await generate_briefing(period)
    except Exception as exc:
        logger.error("Briefing generation crashed: period=%s, error=%s", period, exc, exc_info=True)
        await send_slack_alert(
            f":x: *브리핑 생성 실패*\n- 시간대: {period}\n- 에러: {str(exc)[:200]}"
        )


async def generate_briefing(period: str) -> None:
    """
    브리핑 생성 파이프라인.
    뉴스 수집 → AI 요약 → TTS 변환 → R2 업로드 → DB 저장
    ACID 보장: get_db_context로 트랜잭션 관리.
    """
    today = datetime.now(KST).date()
    logger.info("=== Briefing pipeline start: period=%s, date=%s ===", period, today)

    async with get_db_context() as db:
        # 이미 완료된 브리핑이 있으면 스킵
        stmt = select(Briefing).where(
            Briefing.period == period,
            Briefing.scheduled_date == today,
            Briefing.status == "completed",
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            logger.info("Briefing already exists: period=%s, date=%s. Skip.", period, today)
            return

        # DB에 generating 레코드 생성
        briefing = Briefing(period=period, scheduled_date=today, status="generating")
        db.add(briefing)
        await db.flush()
        briefing_id = briefing.id

        try:
            # 1. 뉴스 수집
            fetcher = NaverNewsFetcher()
            articles = await fetcher.fetch_briefing_articles(period)
            await fetcher.close()

            if not articles:
                raise RuntimeError(f"No articles fetched for period: {period}")

            # 2. AI 요약
            summarizer = GeminiSummarizer()
            script, metadata = await summarizer.summarize_articles(articles, period, db)

            # 3. TTS 변환 (설정의 기본 음성 사용)
            _voice_id = _get_settings().DEFAULT_VOICE_ID
            tts = SupertoneTTS()
            audio_bytes, duration = await tts.text_to_speech(script, db, voice_id=_voice_id)

            # 4. Supabase Storage 업로드
            storage = SupabaseStorage()
            object_key = SupabaseStorage.generate_object_key(period, today.isoformat())
            audio_url = await storage.upload_audio(audio_bytes, object_key)

            # 5. DB 업데이트 (원자적)
            briefing.title = metadata.get("title", f"{period} 브리핑")
            briefing.script = script
            briefing.audio_url = audio_url
            briefing.audio_duration_seconds = duration
            briefing.status = "completed"
            briefing.article_count = len(articles)
            briefing.generated_at = datetime.now(timezone.utc)

            # 기사 저장
            article_summaries = {
                s["index"]: s["summary"]
                for s in metadata.get("article_summaries", [])
            }
            for i, a in enumerate(articles):
                article = BriefingArticle(
                    briefing_id=briefing_id,
                    title=a.get("title", ""),
                    original_url=a.get("link", ""),
                    summary=article_summaries.get(i, a.get("description", "")),
                    full_content=a.get("description", ""),
                    category=a.get("category"),
                    source=a.get("source", ""),
                    thumbnail_url=a.get("thumbnail_url"),
                    video_url=a.get("video_url"),
                    display_order=i,
                    published_at=None,
                )
                db.add(article)

            # 트랜잭션 커밋은 get_db_context가 처리
            logger.info(
                "=== Briefing complete: id=%s, period=%s, articles=%d, duration=%ds ===",
                briefing_id, period, len(articles), duration,
            )

            # 6. 빌링 모니터링
            await check_daily_gemini_usage(db)
            await check_monthly_supertone_usage(db)

            # 7. FCM 푸시 알림 (알림 허용 + FCM 토큰 보유 사용자)
            await _send_briefing_push_notifications(briefing.title or f"{period} 브리핑")

        except Exception as exc:
            briefing.status = "failed"
            briefing.retry_count += 1
            briefing.error_message = str(exc)[:500]
            logger.error("Briefing failed: id=%s, error=%s", briefing_id, exc, exc_info=True)
            raise


async def _send_briefing_push_notifications(briefing_title: str) -> None:
    """알림을 허용한 사용자들에게 브리핑 완료 FCM 푸시를 발송합니다."""
    try:
        settings = _get_settings()
        if not settings.FCM_SERVER_KEY:
            logger.debug("FCM_SERVER_KEY 미설정 — 푸시 알림 건너뜀.")
            return

        fcm = FCMService(settings.FCM_SERVER_KEY)
        async with get_db_context() as db:
            stmt = (
                select(User.fcm_token)
                .where(
                    User.is_active.is_(True),
                    User.notification_enabled.is_(True),
                    User.fcm_token.isnot(None),
                )
            )
            tokens = (await db.execute(stmt)).scalars().all()

        if not tokens:
            logger.debug("FCM 토큰 보유 사용자 없음 — 푸시 알림 건너뜀.")
            return

        result = await fcm.send_to_tokens(
            list(tokens),
            title="브리핑 준비됨",
            body=f"{briefing_title} - 지금 들어보세요",
            data={"type": "briefing_ready"},
        )
        logger.info(
            "FCM 푸시 발송 완료: success=%d, failure=%d",
            result["success"],
            result["failure"],
        )
    except Exception as exc:
        logger.error("FCM 푸시 발송 오류: %s", exc)


async def _check_expired_subscriptions() -> None:
    """만료된 구독을 처리합니다."""
    try:
        async with get_db_context() as db:
            count = await check_expired_subscriptions(db)
            if count:
                logger.info("Processed %d expired subscriptions", count)
    except Exception as exc:
        logger.error("Subscription check failed: %s", exc)


async def _update_weekly_trends() -> None:
    """오늘 브리핑에 포함된 기사들의 키워드 트렌드를 갱신합니다."""
    try:
        async with get_db_context() as db:
            today = datetime.now(KST).date()
            stmt = (
                select(Briefing)
                .where(Briefing.scheduled_date == today, Briefing.status == "completed")
            )
            briefings = (await db.execute(stmt)).scalars().all()

            all_articles = []
            for b in briefings:
                if b.script:
                    all_articles.append({"title": b.title or "", "description": b.script})

            if all_articles:
                await save_weekly_trends(db, all_articles)
                logger.info("Weekly trends updated with %d briefing scripts", len(all_articles))
    except Exception as exc:
        logger.error("Trend update failed: %s", exc)
