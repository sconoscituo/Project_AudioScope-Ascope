"""
Gemini AI 뉴스 요약 서비스 모듈.
수집된 기사를 한국어 오디오 브리핑 스크립트로 요약합니다.
비용 추적 및 개별 기사 요약 기능을 포함합니다.
"""

import json
import logging
import threading
from datetime import datetime, timedelta, timezone

import google.generativeai as genai
from sqlalchemy.ext.asyncio import AsyncSession

KST = timezone(timedelta(hours=9))

from app.config import get_settings
from app.models.billing import BillingUsage

logger = logging.getLogger(__name__)
settings = get_settings()

GEMINI_INPUT_COST_PER_TOKEN = 0.000_000_075
GEMINI_OUTPUT_COST_PER_TOKEN = 0.000_000_300

BRIEFING_SYSTEM_PROMPT = """당신은 AudioScope의 AI 뉴스 앵커 '스코프'입니다.
당신의 이름은 스코프이며, 청취자들에게 친근하면서도 신뢰감 있는 뉴스를 전달합니다.
제공된 뉴스 기사들을 바탕으로 자연스럽고 프로페셔널한 한국어 오디오 브리핑 스크립트를 작성하세요.

요구사항:
- 분량: 4~6분 낭독 분량 (약 800~1200자)
- 문체: 격식체(~습니다, ~입니다), 뉴스 앵커 톤이지만 너무 딱딱하지 않게
- 구성:
  1. 인사말: "안녕하세요, AudioScope 스코프입니다. 오늘 [시간대] 뉴스 [N]건을 분석하여 핵심만 전해드리겠습니다."
  2. [CHAPTER:기사제목] 마커와 함께 주요 뉴스 4~6개 전달
  3. 각 뉴스는 핵심 2~3문장 + 자연스러운 전환
  4. 마무리: "이상 AudioScope 스코프였습니다. [시간대에 맞는 인사]"
- 각 뉴스 시작 전에 반드시 [CHAPTER:기사제목] 형태의 챕터 마커 삽입
- 출처 URL은 절대 포함하지 않음
- TTS에 적합하도록 특수문자, 괄호, 약어 최소화
- 숫자는 한국어로 읽기 쉽게 표현 (예: 1,200억 → 천이백억)
- 신뢰 구축: 분석한 기사 수를 인사말에 자연스럽게 언급

추가로 JSON 형태의 메타데이터도 생성하세요:
{
  "title": "브리핑 제목 (10자 이내)",
  "article_summaries": [
    {"index": 0, "summary": "개별 기사 2-3문장 요약"}
  ]
}

응답 형식:
---SCRIPT---
(브리핑 스크립트)
---META---
(JSON 메타데이터)
"""


import threading


class GeminiSummarizer:
    """Gemini API를 사용한 뉴스 요약 서비스 (thread-safe singleton)."""

    _instance: "GeminiSummarizer | None" = None
    _lock = threading.Lock()

    def __new__(cls) -> "GeminiSummarizer":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._initialized = False
                    cls._instance = instance
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self._model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                system_instruction=BRIEFING_SYSTEM_PROMPT,
            )
        else:
            self._model = None
            logger.warning("GEMINI_API_KEY not set. Summarizer will use fallback.")
        self._initialized = True
        logger.info("GeminiSummarizer initialized.")

    async def summarize_articles(
        self,
        articles: list[dict],
        period: str,
        db: AsyncSession,
    ) -> tuple[str, dict]:
        """
        기사 목록을 받아 브리핑 스크립트 + 메타데이터를 생성합니다.

        Returns:
            tuple[str, dict]: (브리핑 스크립트, 메타데이터 dict)
        """
        period_kr = {"morning": "아침", "lunch": "점심", "evening": "저녁"}.get(period, period)
        articles_text = "\n\n".join(
            f"[기사 {i+1}] [{a.get('category', '기타')}]\n"
            f"제목: {a.get('title', '')}\n"
            f"내용: {a.get('description', '')}"
            for i, a in enumerate(articles[:settings.MAX_ARTICLES_PER_BRIEFING])
        )
        prompt = f"오늘 {period_kr} 브리핑을 위한 다음 기사들을 요약해주세요:\n\n{articles_text}"

        if self._model is None:
            return self._fallback_script(articles, period_kr), {"title": f"{period_kr} 브리핑", "article_summaries": []}

        try:
            response = await self._model.generate_content_async(prompt)
            raw_text = response.text

            script, metadata = self._parse_response(raw_text, period_kr)

            logger.info(
                "Gemini summarization complete: period=%s, script_length=%d",
                period, len(script),
            )

            # 비용 추적
            cost_usd = await self._track_cost(response, db)

            return script, metadata

        except Exception as exc:
            logger.error("Gemini API call failed: %s", exc, exc_info=True)
            return self._fallback_script(articles, period_kr), {"title": f"{period_kr} 브리핑", "article_summaries": []}

    def _parse_response(self, raw_text: str, period_kr: str) -> tuple[str, dict]:
        """Gemini 응답에서 스크립트와 메타데이터를 분리합니다."""
        script = raw_text
        metadata: dict = {"title": f"{period_kr} 브리핑", "article_summaries": []}

        if "---SCRIPT---" in raw_text and "---META---" in raw_text:
            parts = raw_text.split("---META---")
            script = parts[0].replace("---SCRIPT---", "").strip()
            if len(parts) > 1:
                try:
                    meta_text = parts[1].strip()
                    # JSON 블록 추출
                    if "```" in meta_text:
                        meta_text = meta_text.split("```")[1]
                        if meta_text.startswith("json"):
                            meta_text = meta_text[4:]
                    metadata = json.loads(meta_text.strip())
                except (json.JSONDecodeError, IndexError):
                    logger.warning("Failed to parse metadata JSON, using defaults")

        return script, metadata

    @staticmethod
    def _fallback_script(articles: list[dict], period_kr: str) -> str:
        """Gemini 사용 불가 시 간단한 폴백 스크립트를 생성합니다."""
        lines = [f"AudioScope, 오늘의 {period_kr} 브리핑입니다.\n"]
        for i, a in enumerate(articles[:5]):
            lines.append(f"{i+1}번째 소식입니다. {a.get('title', '')}. {a.get('description', '')}\n")
        lines.append("이상 AudioScope였습니다. 좋은 하루 보내세요.")
        return "\n".join(lines)

    @staticmethod
    async def _track_cost(response: object, db: AsyncSession) -> float:
        """Gemini 사용 비용을 DB에 기록합니다."""
        usage_meta = getattr(response, "usage_metadata", None)
        if not usage_meta:
            return 0.0
        input_tokens = getattr(usage_meta, "prompt_token_count", 0) or 0
        output_tokens = getattr(usage_meta, "candidates_token_count", 0) or 0
        cost_usd = (
            input_tokens * GEMINI_INPUT_COST_PER_TOKEN
            + output_tokens * GEMINI_OUTPUT_COST_PER_TOKEN
        )
        record = BillingUsage(
            service="gemini",
            usage_date=datetime.now(KST).date(),
            amount_usd=cost_usd,
            request_count=1,
            metadata_json=json.dumps({"input_tokens": input_tokens, "output_tokens": output_tokens}),
        )
        db.add(record)
        await db.flush()
        logger.info("Gemini cost: $%.6f (in=%d, out=%d tokens)", cost_usd, input_tokens, output_tokens)
        return cost_usd
