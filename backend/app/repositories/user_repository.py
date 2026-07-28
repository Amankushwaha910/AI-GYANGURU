"""
User repository — user-specific database queries.
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import Profile, User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(
            select(User)
            .where(User.email == email.lower())
            .options(selectinload(User.profile))
        )
        return result.scalar_one_or_none()

    async def get_by_google_id(self, google_id: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.google_id == google_id)
        )
        return result.scalar_one_or_none()

    async def get_with_profile(self, user_id: UUID) -> Optional[User]:
        result = await self.db.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.profile))
        )
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        result = await self.db.execute(
            select(User.id).where(User.email == email.lower())
        )
        return result.scalar_one_or_none() is not None


class ProfileRepository(BaseRepository[Profile]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Profile, db)

    async def get_by_user_id(self, user_id: UUID) -> Optional[Profile]:
        result = await self.db.execute(
            select(Profile).where(Profile.user_id == user_id)
        )
        return result.scalar_one_or_none()
