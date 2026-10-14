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

        # Return the filtered total alongside page rows without a second
        # pooler round trip. An empty/out-of-range page has no window value,
        # so preserve exact pagination semantics with the count fallback.
        page_query = query.add_columns(func.count().over().label("total"))
        page_query = page_query.order_by(HistoryItem.created_at.desc())
        page_query = page_query.limit(page_size).offset((page - 1) * page_size)

        rows = (await self.db.execute(page_query)).all()
        if rows:
            return [row[0] for row in rows], rows[0][1]

        total = (
            await self.db.execute(
                select(func.count()).select_from(query.subquery())
            )
        ).scalar_one()
        return [], total

    async def get_recent_user_history(self, user_id: UUID, limit: int = 10) -> List[HistoryItem]:
        """Fetch recent activity without the total-count query used by paginated history."""
        result = await self.db.execute(
            select(HistoryItem)
            .where(HistoryItem.user_id == user_id)
            .order_by(HistoryItem.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def add_entry(
        self,
        user_id: UUID,
        item_type: HistoryItemType,
        topic: str,
        resource_id: str,
    ) -> HistoryItem:
        return await self.create_without_refresh(
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
