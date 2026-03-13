"""
Gemini AI 뉴스 요약 서비스 모듈.
수집된 기사를 한국어 오디오 브리핑 스크립트로 요약합니다.
비용 추적 기능을 포함합니다.
"""

import logging
from datetime import date, datetime, timezone
from functools import lru_cache

import google.generativeai as genai
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.billing import BillingUsage

logger = logging.getLogger(__name__)
settings = get_settings()

# Gemini 모델 입력 토큰당 비용 (Gemini 2.5 Flash 기준, USD)
GEMINI_INPUT_COST_PER_TOKEN = 0.000_000_075
GEMINI_OUTPUT_COST_PER_TOKEN = 0.000_000_300

BRIEFING_SYSTEM_PROMPT = """당신은 전문 뉴스 앵커입니다.
제공된 뉴스 기사들을 바탕으로 청취자를 위한 자연스럽고 친근한 한국어 오디오 브리핑 스크립트를 작성하세요.

요구사항:
- 분량: 3~5분 낭독 분량 (약 600~900자)
- 문체: 격식체(~습니다, ~입니다), 뉴스 앵커 톤
- 구성: 인사말 → 주요 뉴스 3~5개 → 마무리 인사
- 각 뉴스는 핵심 내용만 2~3문장으로 요약
- 출처 URL은 포함하지 않음
- TTS에 적합하도록 특수문자 최소화
"""


class GeminiSummarizer:
    """Gemini API를 사용한 뉴스 요약 서비스 (싱글톤)."""

    _instance: "GeminiSummarizer | None" = None

    def __new__(cls) -> "GeminiSummarizer":
        """싱글톤 인스턴스를 반환합니다."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Gemini 클라이언트를 초기화합니다 (최초 1회)."""
        if self._initialized:
            return
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self._model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=BRIEFING_SYSTEM_PROMPT,
        )
        self._initialized = True
        logger.info("GeminiSummarizer initialized.")

    async def summarize_articles(
        self,
        articles: list[dict],
        period: str,
        db: AsyncSession,
    ) -> str:
        """
        기사 목록을 받아 한국어 오디오 브리핑 스크립트를 생성합니다.

        Args:
            articles: 기사 dict 목록 (title, description 필드 필요)
            period: 브리핑 기간 ('morning', 'lunch', 'evening')
            db: DB 세션 (빌링 기록용)

        Returns:
            str: 생성된 브리핑 스크립트 텍스트

        Raises:
            RuntimeError: Gemini API 호출 실패 시
        """
        period_kr = {"morning": "아침", "lunch": "점심", "evening": "저녁"}.get(period, period)
        articles_text = "\n\n".join(
            f"[기사 {i+1}]\n제목: {a.get('title', '')}\n내용: {a.get('description', '')}"
            for i, a in enumerate(articles[:10])
        )
        prompt = f"오늘 {period_kr} 브리핑을 위한 다음 기사들을 요약해주세요:\n\n{articles_text}"

        try:
            response = await self._model.generate_content_async(prompt)
            script = response.text
            logger.info(
                "Gemini summarization complete for period '%s', script length: %d",
                period, len(script),
            )

            # 비용 추적
            usage_meta = getattr(response, "usage_metadata", None)
            if usage_meta:
                input_tokens = getattr(usage_meta, "prompt_token_count", 0) or 0
                output_tokens = getattr(usage_meta, "candidates_token_count", 0) or 0
                cost_usd = (
                    input_tokens * GEMINI_INPUT_COST_PER_TOKEN
                    + output_tokens * GEMINI_OUTPUT_COST_PER_TOKEN
                )
                await self._record_billing(db, cost_usd)
                logger.info(
                    "Gemini usage: input=%d tokens, output=%d tokens, cost=$%.6f",
                    input_tokens, output_tokens, cost_usd,
                )

            return script
        except Exception as exc:
            logger.error("Gemini API call failed: %s", exc, exc_info=True)
            raise RuntimeError(f"Gemini summarization failed: {exc}") from exc

    @staticmethod
    async def _record_billing(db: AsyncSession, amount_usd: float) -> None:
        """
        Gemini 사용 비용을 DB에 기록합니다.

        Args:
            db: DB 세션
            amount_usd: 사용 비용 (USD)
        """
        record = BillingUsage(
            service="gemini",
            usage_date=date.today(),
            amount_usd=amount_usd,
            request_count=1,
        )
        db.add(record)
        await db.flush()
        logger.debug("Billing recorded: gemini $%.6f", amount_usd)
