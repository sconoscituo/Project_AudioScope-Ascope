"""
Cloudflare R2 오브젝트 스토리지 서비스 모듈.
오디오 파일 업로드/삭제 및 공개 URL 생성을 담당합니다.
"""

import logging
from datetime import datetime

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

R2_ENDPOINT_URL = f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"


class R2Storage:
    """Cloudflare R2 스토리지 클라이언트 (싱글톤, boto3 사용)."""

    _instance: "R2Storage | None" = None

    def __new__(cls) -> "R2Storage":
        """싱글톤 인스턴스를 반환합니다."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """R2 boto3 클라이언트를 초기화합니다 (최초 1회)."""
        if self._initialized:
            return
        self._client = boto3.client(
            "s3",
            endpoint_url=R2_ENDPOINT_URL,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            region_name="auto",
        )
        self._bucket = settings.R2_BUCKET_NAME
        self._initialized = True
        logger.info("R2Storage initialized. Bucket: %s", self._bucket)

    async def upload_audio(self, file_bytes: bytes, object_key: str) -> str:
        """
        오디오 데이터를 R2 버킷에 업로드하고 공개 URL을 반환합니다.

        Args:
            file_bytes: 업로드할 mp3 오디오 데이터
            object_key: R2 버킷 내 저장 경로 (예: briefings/2024-01-01/morning.mp3)

        Returns:
            str: 공개 접근 가능한 오디오 URL

        Raises:
            RuntimeError: 업로드 실패 시
        """
        try:
            self._client.put_object(
                Bucket=self._bucket,
                Key=object_key,
                Body=file_bytes,
                ContentType="audio/mpeg",
            )
            public_url = f"{settings.R2_PUBLIC_URL.rstrip('/')}/{object_key}"
            logger.info(
                "Audio uploaded to R2: key=%s, size=%d bytes, url=%s",
                object_key, len(file_bytes), public_url,
            )
            return public_url
        except (BotoCoreError, ClientError) as exc:
            logger.error("R2 upload failed for key '%s': %s", object_key, exc, exc_info=True)
            raise RuntimeError(f"R2 upload failed: {exc}") from exc

    async def delete_audio(self, object_key: str) -> bool:
        """
        R2 버킷에서 오디오 파일을 삭제합니다.

        Args:
            object_key: 삭제할 R2 오브젝트 키

        Returns:
            bool: 삭제 성공 여부
        """
        try:
            self._client.delete_object(Bucket=self._bucket, Key=object_key)
            logger.info("Audio deleted from R2: key=%s", object_key)
            return True
        except (BotoCoreError, ClientError) as exc:
            logger.error("R2 delete failed for key '%s': %s", object_key, exc, exc_info=True)
            return False

    @staticmethod
    def generate_object_key(period: str, date_str: str) -> str:
        """
        R2 저장 경로(오브젝트 키)를 생성합니다.

        Args:
            period: 브리핑 기간 ('morning', 'lunch', 'evening')
            date_str: 날짜 문자열 (YYYY-MM-DD 형식)

        Returns:
            str: R2 오브젝트 키 (예: briefings/2024-01-01/morning.mp3)
        """
        return f"briefings/{date_str}/{period}.mp3"
