"""
Summary repository.
"""
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.summary import Summary
from app.repositories.base_repository import BaseRepository


class SummaryRepository(BaseRepository[Summary]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Summary, db)

    async def get_user_summaries(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
    ) -> Tuple[List[Summary], int]:
        query = select(Summary).where(Summary.user_id == user_id)

        if search:
            query = query.where(Summary.topic.ilike(f"%{search}%"))

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar_one()

        query = query.order_by(Summary.created_at.desc())
        query = query.limit(page_size).offset((page - 1) * page_size)

        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def get_user_summary(self, user_id: UUID, summary_id: UUID) -> Optional[Summary]:
        result = await self.db.execute(
            select(Summary).where(
                Summary.id == summary_id,
                Summary.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def count_for_user(self, user_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count()).where(Summary.user_id == user_id)
        )
        return result.scalar_one()
