"""
Firebase Storage 서비스 모듈.
오디오 파일 업로드/삭제 및 공개 URL 생성을 담당합니다.
firebase-admin SDK를 asyncio executor로 래핑하여 이벤트 루프 블로킹을 방지합니다.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import partial

import firebase_admin
from firebase_admin import storage as firebase_storage

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="fb-storage")


class FirebaseStorage:
    """Firebase Storage 클라이언트."""

    _instance: "FirebaseStorage | None" = None

    def __new__(cls) -> "FirebaseStorage":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        try:
            self._bucket = firebase_storage.bucket(
                app=firebase_admin.get_app(),
                name=settings.FIREBASE_STORAGE_BUCKET or None,
            )
            logger.info("FirebaseStorage initialized. Bucket: %s", self._bucket.name)
        except Exception as exc:
            self._bucket = None
            logger.warning("FirebaseStorage init failed: %s. Storage disabled.", exc)
        self._initialized = True

    async def upload_audio(self, file_bytes: bytes, object_key: str) -> str:
        """오디오를 Firebase Storage에 업로드하고 공개 URL을 반환합니다."""
        if not self._bucket:
            logger.warning("Firebase Storage not configured. Returning placeholder URL.")
            return f"https://placeholder.storage/{object_key}"

        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(
                _executor,
                partial(self._upload_sync, file_bytes, object_key),
            )
            public_url = (
                f"https://storage.googleapis.com/{self._bucket.name}/{object_key}"
            )
            logger.info(
                "Firebase upload: key=%s, size=%d bytes", object_key, len(file_bytes)
            )
            return public_url
        except Exception as exc:
            logger.error("Firebase upload failed: key=%s, error=%s", object_key, exc)
            raise RuntimeError(f"Firebase Storage upload failed: {exc}") from exc

    def _upload_sync(self, file_bytes: bytes, object_key: str) -> None:
        blob = self._bucket.blob(object_key)
        blob.upload_from_string(file_bytes, content_type="audio/mpeg")
        blob.make_public()

    async def delete_audio(self, object_key: str) -> bool:
        """Firebase Storage에서 오디오 파일을 삭제합니다."""
        if not self._bucket:
            return False
        loop = asyncio.get_running_loop()
        try:
            blob = self._bucket.blob(object_key)
            await loop.run_in_executor(_executor, blob.delete)
            logger.info("Firebase delete: key=%s", object_key)
            return True
        except Exception as exc:
            logger.error("Firebase delete failed: key=%s, error=%s", object_key, exc)
            return False

    @staticmethod
    def generate_object_key(period: str, date_str: str) -> str:
        return f"briefings/{date_str}/{period}.mp3"
