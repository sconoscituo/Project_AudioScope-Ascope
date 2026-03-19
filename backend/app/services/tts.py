"""
Supertone Play TTS 서비스 모듈.
텍스트를 음성(mp3)으로 변환하고 비용을 추적합니다.
긴 텍스트는 청크 분할 후 병합합니다.
"""

import logging
import threading
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.billing import BillingUsage

logger = logging.getLogger(__name__)
settings = get_settings()

KST = timezone(timedelta(hours=9))
SUPERTONE_API_URL = "https://api.supertone.ai/v1/text-to-speech"
SUPERTONE_COST_PER_REQUEST = 0.05
MAX_TTS_CHARS = 3000


class SupertoneTTS:
    """Supertone Play API를 사용하는 TTS 서비스 (thread-safe singleton)."""

    _instance: "SupertoneTTS | None" = None
    _lock = threading.Lock()

    def __new__(cls) -> "SupertoneTTS":
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
        self._headers = {
            "Authorization": f"Bearer {settings.SUPERTONE_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }
        self._client: httpx.AsyncClient | None = None
        self._initialized = True
        logger.info("SupertoneTTS initialized.")

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(180.0, connect=10.0))
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def text_to_speech(
        self,
        text: str,
        db: AsyncSession,
        voice_id: str = "ko-KR-female-1",
        speed: float = 1.0,
    ) -> tuple[bytes, int]:
        """
        텍스트를 음성(mp3 bytes)으로 변환합니다.

        Returns:
            tuple[bytes, int]: (mp3 오디오 데이터, 예상 재생 시간 초)
        """
        if not settings.SUPERTONE_API_KEY:
            logger.warning("SUPERTONE_API_KEY not set. Returning empty audio.")
            return b"", 0

        # 긴 텍스트는 청크로 분할
        chunks = self._split_text(text, MAX_TTS_CHARS)
        audio_parts: list[bytes] = []

        for i, chunk in enumerate(chunks):
            logger.info("TTS chunk %d/%d: %d chars", i + 1, len(chunks), len(chunk))
            audio_bytes = await self._synthesize_chunk(chunk, voice_id, speed)
            audio_parts.append(audio_bytes)

        combined = b"".join(audio_parts)
        # 대략적인 재생 시간 추정 (한국어 기준 분당 약 300자)
        estimated_duration = int(len(text) / 300 * 60)

        await self._record_billing(db, SUPERTONE_COST_PER_REQUEST * len(chunks))

        logger.info(
            "TTS complete: text=%d chars, audio=%d bytes, ~%ds",
            len(text), len(combined), estimated_duration,
        )
        return combined, estimated_duration

    async def _synthesize_chunk(
        self, text: str, voice_id: str, speed: float
    ) -> bytes:
        """단일 텍스트 청크를 음성으로 변환합니다."""
        payload = {
            "text": text,
            "voice_id": voice_id,
            "speed": speed,
            "output_format": "mp3",
        }
        try:
            client = await self._get_client()
            response = await client.post(
                SUPERTONE_API_URL, json=payload, headers=self._headers,
            )
            response.raise_for_status()
            return response.content
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Supertone API error: status=%d", exc.response.status_code,
            )
            raise RuntimeError(f"Supertone TTS failed: {exc}") from exc
        except Exception as exc:
            logger.error("Supertone TTS error: %s", exc)
            raise RuntimeError(f"Supertone TTS failed: {exc}") from exc

    @staticmethod
    def _split_text(text: str, max_chars: int) -> list[str]:
        """텍스트를 문장 단위로 청크 분할합니다."""
        if len(text) <= max_chars:
            return [text]

        chunks: list[str] = []
        current = ""
        sentences = text.replace(".\n", ". \n").split(". ")

        for sentence in sentences:
            candidate = f"{current}. {sentence}" if current else sentence
            if len(candidate) > max_chars and current:
                chunks.append(current.strip())
                current = sentence
            else:
                current = candidate

        if current.strip():
            chunks.append(current.strip())

        return chunks if chunks else [text]

    @staticmethod
    async def _record_billing(db: AsyncSession, amount_usd: float) -> None:
        record = BillingUsage(
            service="supertone",
            usage_date=datetime.now(KST).date(),
            amount_usd=amount_usd,
            request_count=1,
        )
        db.add(record)
        await db.flush()
