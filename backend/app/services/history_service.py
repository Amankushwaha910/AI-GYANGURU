"""
History service — browsing and management of learning history.
"""
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.history import HistoryItem, HistoryItemType
from app.repositories.history_repository import HistoryRepository


class HistoryService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.history_repo = HistoryRepository(db)

    async def get_history(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        item_type: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[HistoryItem], int]:
        parsed_type = HistoryItemType(item_type) if item_type else None
        return await self.history_repo.get_user_history(
            user_id=user_id,
            page=page,
            page_size=page_size,
            item_type=parsed_type,
            search=search,
        )

    async def delete_item(self, user_id: UUID, item_id: UUID) -> None:
        item = await self.history_repo.get_by_id(item_id)
        if not item or item.user_id != user_id:
            raise NotFoundError("History item", str(item_id))
        await self.history_repo.delete(item)

    async def clear_by_type(self, user_id: UUID, item_type: str) -> int:
        parsed_type = HistoryItemType(item_type)
        return await self.history_repo.delete_by_type(user_id, parsed_type)
