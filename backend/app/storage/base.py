"""
Abstract storage provider interface.
Swapping storage (Supabase → S3) requires only a new implementation.
"""
from abc import ABC, abstractmethod


class BaseStorageClient(ABC):
    @abstractmethod
    async def upload(
        self,
        bucket: str,
        user_id: str,
        filename: str,
        content: bytes,
        mime_type: str,
    ) -> str:
        """Upload file and return the storage path."""
        ...

    @abstractmethod
    async def get_signed_url(self, bucket: str, path: str, expires_in: int = 3600) -> str:
        """Return a time-limited signed URL for the given path."""
        ...

    @abstractmethod
    async def delete(self, bucket: str, path: str) -> None:
        """Delete a file from storage."""
        ...
