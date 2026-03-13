"""
빌링 모니터링 서비스 모듈.
Gemini/Supertone 사용량이 한도를 초과하면 Slack으로 알림을 발송합니다.
"""

import logging
from calendar import monthrange
from datetime import date

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.billing import BillingUsage

logger = logging.getLogger(__name__)
settings = get_settings()


async def check_daily_gemini_usage(db: AsyncSession) -> None:
    """
    오늘 Gemini API 사용량이 일일 한도를 초과했는지 확인하고,
    초과 시 Slack 알림을 발송합니다.

    Args:
        db: DB 세션
    """
    today = date.today()
    stmt = select(func.sum(BillingUsage.amount_usd)).where(
        BillingUsage.service == "gemini",
        BillingUsage.usage_date == today,
    )
    result = await db.execute(stmt)
    total_usd: float = result.scalar_one_or_none() or 0.0

    logger.info("Gemini daily usage: $%.4f / $%.2f limit", total_usd, settings.GEMINI_DAILY_LIMIT_USD)

    if total_usd >= settings.GEMINI_DAILY_LIMIT_USD:
        message = (
            f":warning: *AudioScope 빌링 경보*\n"
            f"Gemini API 일일 사용량이 한도를 초과했습니다.\n"
            f"• 오늘 사용량: ${total_usd:.4f}\n"
            f"• 일일 한도: ${settings.GEMINI_DAILY_LIMIT_USD:.2f}\n"
            f"• 날짜: {today}"
        )
        await send_slack_alert(message)
        logger.warning("Gemini daily limit exceeded: $%.4f", total_usd)


async def check_monthly_supertone_usage(db: AsyncSession) -> None:
    """
    이번 달 Supertone API 사용량이 월간 한도를 초과했는지 확인하고,
    초과 시 Slack 알림을 발송합니다.

    Args:
        db: DB 세션
    """
    today = date.today()
    month_start = date(today.year, today.month, 1)

    stmt = select(func.sum(BillingUsage.amount_usd)).where(
        BillingUsage.service == "supertone",
        BillingUsage.usage_date >= month_start,
        BillingUsage.usage_date <= today,
    )
    result = await db.execute(stmt)
    total_usd: float = result.scalar_one_or_none() or 0.0

    logger.info(
        "Supertone monthly usage: $%.4f / $%.2f limit",
        total_usd, settings.SUPERTONE_MONTHLY_LIMIT_USD,
    )

    if total_usd >= settings.SUPERTONE_MONTHLY_LIMIT_USD:
        message = (
            f":rotating_light: *AudioScope 빌링 경보*\n"
            f"Supertone API 월간 사용량이 한도를 초과했습니다.\n"
            f"• 이번 달 사용량: ${total_usd:.4f}\n"
            f"• 월간 한도: ${settings.SUPERTONE_MONTHLY_LIMIT_USD:.2f}\n"
            f"• 기간: {month_start} ~ {today}"
        )
        await send_slack_alert(message)
        logger.warning("Supertone monthly limit exceeded: $%.4f", total_usd)


async def send_slack_alert(message: str) -> None:
    """
    Slack Incoming Webhook으로 알림 메시지를 전송합니다.

    Args:
        message: 전송할 메시지 (Slack markdown 지원)
    """
    if not settings.SLACK_WEBHOOK_URL:
        logger.warning("SLACK_WEBHOOK_URL not configured. Skipping alert: %s", message)
        return

    payload = {"text": message}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(settings.SLACK_WEBHOOK_URL, json=payload)
            response.raise_for_status()
        logger.info("Slack alert sent successfully.")
    except httpx.HTTPStatusError as exc:
        logger.error(
            "Slack webhook HTTP error: status=%d, body=%s",
            exc.response.status_code, exc.response.text,
        )
    except Exception as exc:
        logger.error("Slack alert failed: %s", exc, exc_info=True)
