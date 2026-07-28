"""
Explanation repository.
"""
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.explanation import Explanation
from app.repositories.base_repository import BaseRepository


class ExplanationRepository(BaseRepository[Explanation]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Explanation, db)

    async def get_user_explanations(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
    ) -> Tuple[List[Explanation], int]:
        query = select(Explanation).where(Explanation.user_id == user_id)
        if search:
            query = query.where(Explanation.topic.ilike(f"%{search}%"))

        total = (
            await self.db.execute(
                select(func.count()).select_from(query.subquery())
            )
        ).scalar_one()

        query = query.order_by(Explanation.created_at.desc())
        query = query.limit(page_size).offset((page - 1) * page_size)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def get_user_explanation(
        self, user_id: UUID, explanation_id: UUID
    ) -> Optional[Explanation]:
        result = await self.db.execute(
            select(Explanation).where(
                Explanation.id == explanation_id,
                Explanation.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def count_for_user(self, user_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count()).where(Explanation.user_id == user_id)
        )
        return result.scalar_one()
