"""
Supertone Play TTS 서비스 모듈.
텍스트를 음성(mp3)으로 변환하고 비용을 추적합니다.
"""

import logging
from datetime import date

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.billing import BillingUsage

logger = logging.getLogger(__name__)
settings = get_settings()

SUPERTONE_API_URL = "https://api.supertone.ai/v1/text-to-speech"

# Supertone 분당 비용 추정 (USD) - 실제 플랜에 맞게 조정
SUPERTONE_COST_PER_REQUEST = 0.05


class SupertoneTTS:
    """Supertone Play API를 사용하는 TTS 서비스 (싱글톤)."""

    _instance: "SupertoneTTS | None" = None

    def __new__(cls) -> "SupertoneTTS":
        """싱글톤 인스턴스를 반환합니다."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Supertone TTS 클라이언트를 초기화합니다 (최초 1회)."""
        if self._initialized:
            return
        self._headers = {
            "Authorization": f"Bearer {settings.SUPERTONE_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }
        self._initialized = True
        logger.info("SupertoneTTS initialized.")

    async def text_to_speech(
        self,
        text: str,
        db: AsyncSession,
        voice_id: str = "ko-KR-female-1",
        speed: float = 1.0,
    ) -> bytes:
        """
        텍스트를 음성(mp3 bytes)으로 변환합니다.

        Args:
            text: 변환할 텍스트 스크립트
            db: DB 세션 (빌링 기록용)
            voice_id: 사용할 음성 ID (기본값: 한국어 여성 1)
            speed: 말하기 속도 (0.5 ~ 2.0)

        Returns:
            bytes: mp3 오디오 데이터

        Raises:
            RuntimeError: Supertone API 호출 실패 시
        """
        payload = {
            "text": text,
            "voice_id": voice_id,
            "speed": speed,
            "output_format": "mp3",
        }
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    SUPERTONE_API_URL,
                    json=payload,
                    headers=self._headers,
                )
                response.raise_for_status()
            audio_bytes = response.content
            logger.info(
                "TTS complete: text_length=%d, audio_size=%d bytes",
                len(text), len(audio_bytes),
            )
            await self._record_billing(db, SUPERTONE_COST_PER_REQUEST)
            return audio_bytes
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Supertone API HTTP error: status=%d, body=%s",
                exc.response.status_code, exc.response.text, exc_info=True,
            )
            raise RuntimeError(f"Supertone TTS failed: {exc}") from exc
        except Exception as exc:
            logger.error("Supertone TTS unexpected error: %s", exc, exc_info=True)
            raise RuntimeError(f"Supertone TTS failed: {exc}") from exc

    @staticmethod
    async def _record_billing(db: AsyncSession, amount_usd: float) -> None:
        """
        Supertone 사용 비용을 DB에 기록합니다.

        Args:
            db: DB 세션
            amount_usd: 사용 비용 (USD)
        """
        record = BillingUsage(
            service="supertone",
            usage_date=date.today(),
            amount_usd=amount_usd,
            request_count=1,
        )
        db.add(record)
        await db.flush()
        logger.debug("Billing recorded: supertone $%.4f", amount_usd)
