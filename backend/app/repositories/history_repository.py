"""
History repository.
"""
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.history import HistoryItem, HistoryItemType
from app.repositories.base_repository import BaseRepository


class HistoryRepository(BaseRepository[HistoryItem]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(HistoryItem, db)

    async def get_user_history(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        item_type: Optional[HistoryItemType] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[HistoryItem], int]:
        query = select(HistoryItem).where(HistoryItem.user_id == user_id)

        if item_type:
            query = query.where(HistoryItem.item_type == item_type)
        if search:
            query = query.where(HistoryItem.topic.ilike(f"%{search}%"))

        total = (
            await self.db.execute(
                select(func.count()).select_from(query.subquery())
            )
        ).scalar_one()

        query = query.order_by(HistoryItem.created_at.desc())
        query = query.limit(page_size).offset((page - 1) * page_size)

        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def add_entry(
        self,
        user_id: UUID,
        item_type: HistoryItemType,
        topic: str,
        resource_id: str,
    ) -> HistoryItem:
        return await self.create(
            user_id=user_id,
            item_type=item_type,
            topic=topic,
            resource_id=resource_id,
        )

    async def delete_by_type(self, user_id: UUID, item_type: HistoryItemType) -> int:
        from sqlalchemy import delete
        result = await self.db.execute(
            delete(HistoryItem).where(
                HistoryItem.user_id == user_id,
                HistoryItem.item_type == item_type,
            )
        )
        return result.rowcount
