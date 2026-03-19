"""
빌링 모니터링 + Slack 알림 서비스 모듈.
빌링 한도 초과, 어뷰징, 문의하기 알림을 Slack Webhook으로 발송합니다.
"""

import logging
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

KST = timezone(timedelta(hours=9))

from app.config import get_settings
from app.models.billing import BillingUsage

logger = logging.getLogger(__name__)
settings = get_settings()


async def check_daily_gemini_usage(db: AsyncSession) -> None:
    """Gemini 일일 사용량 한도 초과 여부를 확인합니다."""
    today = datetime.now(KST).date()
    stmt = select(func.sum(BillingUsage.amount_usd)).where(
        BillingUsage.service == "gemini",
        BillingUsage.usage_date == today,
    )
    result = await db.execute(stmt)
    total_usd: float = result.scalar_one_or_none() or 0.0

    logger.info("Gemini daily usage: $%.4f / $%.2f limit", total_usd, settings.GEMINI_DAILY_LIMIT_USD)

    if total_usd >= settings.GEMINI_DAILY_LIMIT_USD:
        await send_slack_alert(
            f":warning: *빌링 경보* Gemini 일일 한도 초과\n"
            f"- 사용량: ${total_usd:.4f} / ${settings.GEMINI_DAILY_LIMIT_USD:.2f}\n"
            f"- 날짜: {today}"
        )


async def check_monthly_supertone_usage(db: AsyncSession) -> None:
    """Supertone 월간 사용량 한도 초과 여부를 확인합니다."""
    today = datetime.now(KST).date()
    month_start = date(today.year, today.month, 1)

    stmt = select(func.sum(BillingUsage.amount_usd)).where(
        BillingUsage.service == "supertone",
        BillingUsage.usage_date >= month_start,
        BillingUsage.usage_date <= today,
    )
    result = await db.execute(stmt)
    total_usd: float = result.scalar_one_or_none() or 0.0

    if total_usd >= settings.SUPERTONE_MONTHLY_LIMIT_USD:
        await send_slack_alert(
            f":rotating_light: *빌링 경보* Supertone 월간 한도 초과\n"
            f"- 사용량: ${total_usd:.4f} / ${settings.SUPERTONE_MONTHLY_LIMIT_USD:.2f}\n"
            f"- 기간: {month_start} ~ {today}"
        )


async def send_slack_alert(message: str) -> None:
    """Slack Incoming Webhook으로 알림을 전송합니다."""
    if not settings.SLACK_WEBHOOK_URL:
        logger.warning("SLACK_WEBHOOK_URL not set. Alert skipped: %s", message[:100])
        return

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                settings.SLACK_WEBHOOK_URL, json={"text": message}
            )
            response.raise_for_status()
        logger.info("Slack alert sent.")
    except Exception as exc:
        logger.error("Slack alert failed: %s", exc)


async def send_abuse_alert(ip: str, path: str, detail: str) -> None:
    """어뷰징 감지 Slack 알림을 발송합니다."""
    await send_slack_alert(
        f":rotating_light: *어뷰징 감지*\n"
        f"- IP: `{ip}`\n- 경로: `{path}`\n- 상세: {detail}"
    )


async def send_inquiry_alert(
    user_email: str, user_id: str, subject: str, message: str
) -> None:
    """고객 문의 Slack 알림을 발송합니다."""
    await send_slack_alert(
        f":envelope: *고객 문의*\n"
        f"- 사용자: {user_email} (`{user_id}`)\n"
        f"- 제목: {subject}\n"
        f"- 내용: {message[:500]}"
    )
