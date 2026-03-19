"""
브리핑 순수 도메인 모델.
DB(SQLAlchemy) 또는 네트워크(Pydantic) 의존 없이 비즈니스 규칙만 표현합니다.
"""

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass
class BriefingDomain:
    """오디오 브리핑 도메인 모델."""

    period: str                          # 'morning' | 'lunch' | 'evening'
    scheduled_date: date
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    title: str | None = None
    script: str | None = None
    audio_url: str | None = None
    audio_duration_seconds: int | None = None
    status: str = "pending"              # 'pending' | 'processing' | 'completed' | 'failed'
    article_count: int = 0
    generated_at: datetime | None = None
    generation_cost_usd: float = 0.0
    retry_count: int = 0
    error_message: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    # ── 도메인 규칙 ──

    def mark_processing(self) -> None:
        """브리핑 생성 시작 상태로 전환합니다."""
        self.status = "processing"

    def mark_completed(
        self,
        audio_url: str,
        duration: int,
        title: str | None = None,
    ) -> None:
        """브리핑 생성 완료 상태로 전환합니다."""
        self.audio_url = audio_url
        self.audio_duration_seconds = duration
        self.status = "completed"
        self.generated_at = datetime.utcnow()
        if title:
            self.title = title

    def mark_failed(self, error: str) -> None:
        """브리핑 생성 실패 상태로 전환합니다."""
        self.status = "failed"
        self.error_message = error
        self.retry_count += 1

    @property
    def is_retryable(self) -> bool:
        """재시도 가능 여부 (최대 3회)."""
        return self.status == "failed" and self.retry_count < 3

    def __repr__(self) -> str:
        return (
            f"<BriefingDomain id={self.id} period={self.period} "
            f"date={self.scheduled_date} status={self.status}>"
        )
