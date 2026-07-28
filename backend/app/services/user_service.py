"""
User service — profile management, account operations.
"""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthError, NotFoundError
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import ProfileRepository, UserRepository
from app.schemas.user import ProfileUpdateRequest


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.user_repo = UserRepository(db)
        self.profile_repo = ProfileRepository(db)

    async def get_profile(self, user_id: UUID) -> User:
        user = await self.user_repo.get_with_profile(user_id)
        if not user:
            raise NotFoundError("User", str(user_id))
        return user

    async def update_profile(
        self, user_id: UUID, request: ProfileUpdateRequest
    ) -> User:
        profile = await self.profile_repo.get_by_user_id(user_id)
        if not profile:
            raise NotFoundError("Profile", str(user_id))

        update_data = request.model_dump(exclude_none=True)
        await self.profile_repo.update(profile, **update_data)

        return await self.user_repo.get_with_profile(user_id)

    async def change_password(
        self, user: User, current_password: str, new_password: str
    ) -> None:
        if not user.hashed_password:
            raise AuthError("Password change not available for OAuth accounts")

        if not verify_password(current_password, user.hashed_password):
            raise AuthError("Current password is incorrect")

        await self.user_repo.update(
            user, hashed_password=hash_password(new_password)
        )

    async def delete_account(self, user: User) -> None:
        """Soft delete — deactivate account and cascade deletes handle data."""
        await self.user_repo.update(user, is_active=False)
