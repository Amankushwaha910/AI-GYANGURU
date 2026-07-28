"""
User/Profile routes — /api/v1/users
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser
from app.schemas.common import APIResponse
from app.schemas.user import ProfileUpdateRequest, UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=APIResponse[UserResponse])
async def get_profile(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get the current user's full profile."""
    service = UserService(db)
    user = await service.get_profile(current_user.id)
    return APIResponse(data=UserResponse.model_validate(user))


@router.put("/me", response_model=APIResponse[UserResponse])
async def update_profile(
    request: ProfileUpdateRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Update the current user's profile."""
    service = UserService(db)
    user = await service.update_profile(current_user.id, request)
    return APIResponse(data=UserResponse.model_validate(user), message="Profile updated")


@router.delete("/me", response_model=APIResponse[None])
async def delete_account(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Deactivate the current user's account."""
    service = UserService(db)
    await service.delete_account(current_user)
    return APIResponse(message="Account deactivated successfully")
