"""
Supabase Storage 서비스 모듈.
오디오 파일 업로드/삭제 및 공개 URL 생성을 담당합니다.
httpx를 사용하여 Supabase Storage REST API를 호출합니다.
"""

import logging

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class SupabaseStorage:
    """Supabase Storage 클라이언트."""

    _instance: "SupabaseStorage | None" = None

    def __new__(cls) -> "SupabaseStorage":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._url = settings.SUPABASE_URL.rstrip("/")
        self._key = settings.SUPABASE_SERVICE_KEY
        self._bucket = settings.SUPABASE_STORAGE_BUCKET
        self._headers = {
            "Authorization": f"Bearer {self._key}",
            "apikey": self._key,
        }
        self._enabled = bool(self._url and self._key and self._bucket)
        if not self._enabled:
            logger.warning("Supabase Storage not configured. Storage disabled.")
        else:
            logger.info("SupabaseStorage initialized. Bucket: %s", self._bucket)
        self._initialized = True

    async def upload_audio(self, file_bytes: bytes, object_key: str) -> str:
        """오디오를 Supabase Storage에 업로드하고 공개 URL을 반환합니다."""
        if not self._enabled:
            return f"https://placeholder.storage/{object_key}"

        upload_url = f"{self._url}/storage/v1/object/{self._bucket}/{object_key}"
        headers = {**self._headers, "Content-Type": "audio/mpeg"}

        async with httpx.AsyncClient(timeout=180.0) as client:
            try:
                response = await client.post(upload_url, content=file_bytes, headers=headers)
                # 이미 존재하면 upsert
                if response.status_code == 409:
                    response = await client.put(upload_url, content=file_bytes, headers=headers)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                logger.error("Supabase upload failed: key=%s, status=%d", object_key, exc.response.status_code)
                raise RuntimeError(f"Supabase Storage upload failed: {exc}") from exc

        public_url = f"{self._url}/storage/v1/object/public/{self._bucket}/{object_key}"
        logger.info("Supabase upload: key=%s, size=%d bytes", object_key, len(file_bytes))
        return public_url

    async def delete_audio(self, object_key: str) -> bool:
        """Supabase Storage에서 오디오 파일을 삭제합니다."""
        if not self._enabled:
            return False

        delete_url = f"{self._url}/storage/v1/object/{self._bucket}/{object_key}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.delete(delete_url, headers=self._headers)
                response.raise_for_status()
                logger.info("Supabase delete: key=%s", object_key)
                return True
            except httpx.HTTPStatusError as exc:
                logger.error("Supabase delete failed: key=%s, error=%s", object_key, exc)
                return False

    @staticmethod
    def generate_object_key(period: str, date_str: str) -> str:
        return f"briefings/{date_str}/{period}.mp3"
