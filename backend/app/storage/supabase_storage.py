"""
Supabase Storage implementation.
"""
import uuid
from functools import lru_cache

from app.core.config import settings
from app.core.exceptions import FileProcessingError
from app.storage.base import BaseStorageClient


class SupabaseStorageClient(BaseStorageClient):
    def __init__(self) -> None:
        from supabase import create_client
        self._client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key,
        )

    async def upload(
        self,
        bucket: str,
        user_id: str,
        filename: str,
        content: bytes,
        mime_type: str,
    ) -> str:
        """Upload to Supabase Storage under users/{user_id}/{uuid}_{filename}."""
        safe_name = filename.replace(" ", "_")
        storage_path = f"users/{user_id}/{uuid.uuid4()}_{safe_name}"

        try:
            self._client.storage.from_(bucket).upload(
                path=storage_path,
                file=content,
                file_options={"content-type": mime_type},
            )
            return storage_path
        except Exception as exc:
            raise FileProcessingError(f"Storage upload failed: {exc}") from exc

    async def get_signed_url(
        self, bucket: str, path: str, expires_in: int = 3600
    ) -> str:
        try:
            response = self._client.storage.from_(bucket).create_signed_url(
                path, expires_in
            )
            return response["signedURL"]
        except Exception as exc:
            raise FileProcessingError(f"Failed to get signed URL: {exc}") from exc

    async def delete(self, bucket: str, path: str) -> None:
        try:
            self._client.storage.from_(bucket).remove([path])
        except Exception as exc:
            raise FileProcessingError(f"Storage deletion failed: {exc}") from exc


@lru_cache(maxsize=1)
def get_storage_client() -> BaseStorageClient:
    return SupabaseStorageClient()
