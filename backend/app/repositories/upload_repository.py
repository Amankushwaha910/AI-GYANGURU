"""
Upload repository.
"""
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.upload import Upload
from app.repositories.base_repository import BaseRepository


class UploadRepository(BaseRepository[Upload]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Upload, db)

    async def get_user_upload(
        self, user_id: UUID, upload_id: UUID
    ) -> Optional[Upload]:
        result = await self.db.execute(
            select(Upload).where(
                Upload.id == upload_id,
                Upload.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_user_uploads(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Upload], int]:
        query = select(Upload).where(Upload.user_id == user_id)

        total = (
            await self.db.execute(
                select(func.count()).select_from(query.subquery())
            )
        ).scalar_one()

        query = query.order_by(Upload.created_at.desc())
        query = query.limit(page_size).offset((page - 1) * page_size)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total
