"""
User repository — user-specific database queries.
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import Select, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.user import Profile, User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(User, db)

    @staticmethod
    def _get_by_email_statement(email: str) -> Select[tuple[User]]:
        return (
            select(User)
            .where(User.email == email.lower())
            # Login returns UserResponse.profile. Since this is a one-to-one
            # relation, load it in the same round trip instead of issuing a
            # second SELECT via selectinload.
            .options(joinedload(User.profile))
        )

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(self._get_by_email_statement(email))
        return result.scalar_one_or_none()

    async def rotate_refresh_token_hash(
        self,
        user_id: UUID,
        expected_hash: Optional[str],
        replacement_hash: str,
    ) -> bool:
        """Atomically rotate a refresh hash only if the presented token is current."""
        statement = update(User).where(User.id == user_id)
        if expected_hash is None:
            statement = statement.where(User.refresh_token_hash.is_(None))
        else:
            statement = statement.where(User.refresh_token_hash == expected_hash)
        result = await self.db.execute(
            statement.values(refresh_token_hash=replacement_hash).returning(User.id)
        )
        return result.scalar_one_or_none() is not None

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
