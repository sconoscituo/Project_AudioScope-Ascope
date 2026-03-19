"""
TTS 서비스 포트 (인터페이스).
TTS 공급자를 교체 가능하도록 추상화합니다.
"""

from abc import ABCMeta, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession


class AbstractTTSService(metaclass=ABCMeta):
    """텍스트-음성 변환을 위한 추상 서비스 인터페이스."""

    @abstractmethod
    async def text_to_speech(
        self,
        text: str,
        db: AsyncSession,
        voice_id: str = "ko-KR-female-1",
        speed: float = 1.0,
    ) -> tuple[bytes, int]:
        """
        텍스트를 음성(mp3 bytes)으로 변환합니다.

        Args:
            text: 변환할 텍스트
            db: 비용 기록용 DB 세션
            voice_id: 사용할 음성 ID
            speed: 재생 속도 배율

        Returns:
            tuple[bytes, int]: (mp3 오디오 데이터, 예상 재생 시간 초)
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """HTTP 클라이언트 등 리소스를 정리합니다."""
        ...
