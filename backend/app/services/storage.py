"""
Cloudflare R2 오브젝트 스토리지 서비스 모듈.
오디오 파일 업로드/삭제 및 공개 URL 생성을 담당합니다.
동기 boto3를 asyncio executor로 래핑하여 이벤트 루프 블로킹을 방지합니다.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import partial

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# boto3는 동기 라이브러리이므로 ThreadPoolExecutor에서 실행
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="r2-upload")


class R2Storage:
    """Cloudflare R2 스토리지 클라이언트."""

    _instance: "R2Storage | None" = None

    def __new__(cls) -> "R2Storage":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        if settings.R2_ACCOUNT_ID and settings.R2_ACCESS_KEY_ID:
            endpoint_url = f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
            self._client = boto3.client(
                "s3",
                endpoint_url=endpoint_url,
                aws_access_key_id=settings.R2_ACCESS_KEY_ID,
                aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
                region_name="auto",
            )
        else:
            self._client = None
            logger.warning("R2 credentials not set. Storage will be disabled.")
        self._bucket = settings.R2_BUCKET_NAME
        self._initialized = True
        logger.info("R2Storage initialized. Bucket: %s", self._bucket)

    async def upload_audio(self, file_bytes: bytes, object_key: str) -> str:
        """오디오를 R2에 업로드하고 공개 URL을 반환합니다. (non-blocking)"""
        if not self._client:
            logger.warning("R2 not configured. Returning placeholder URL.")
            return f"https://placeholder.cdn/{object_key}"

        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(
                _executor,
                partial(
                    self._client.put_object,
                    Bucket=self._bucket,
                    Key=object_key,
                    Body=file_bytes,
                    ContentType="audio/mpeg",
                    CacheControl="public, max-age=86400",
                ),
            )
            public_url = f"{settings.R2_PUBLIC_URL.rstrip('/')}/{object_key}"
            logger.info("R2 upload: key=%s, size=%d bytes", object_key, len(file_bytes))
            return public_url
        except (BotoCoreError, ClientError) as exc:
            logger.error("R2 upload failed: key=%s, error=%s", object_key, exc)
            raise RuntimeError(f"R2 upload failed: {exc}") from exc

    async def delete_audio(self, object_key: str) -> bool:
        """R2 버킷에서 오디오 파일을 삭제합니다."""
        if not self._client:
            return False
        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(
                _executor,
                partial(self._client.delete_object, Bucket=self._bucket, Key=object_key),
            )
            logger.info("R2 delete: key=%s", object_key)
            return True
        except (BotoCoreError, ClientError) as exc:
            logger.error("R2 delete failed: key=%s, error=%s", object_key, exc)
            return False

    @staticmethod
    def generate_object_key(period: str, date_str: str) -> str:
        return f"briefings/{date_str}/{period}.mp3"
