"""
Auth routes — /api/v1/auth
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser
from app.schemas.auth import (
    GoogleAuthRequest,
    LoginRequest,
    PasswordChangeRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.common import APIResponse
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=APIResponse[TokenResponse], status_code=201)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user account."""
    service = AuthService(db)
    tokens = await service.register(request)
    return APIResponse(data=tokens, message="Registration successful")


@router.post("/login", response_model=APIResponse[TokenResponse])
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate with email and password."""
    service = AuthService(db)
    tokens = await service.login(request)
    return APIResponse(data=tokens, message="Login successful")


@router.post("/refresh", response_model=APIResponse[TokenResponse])
async def refresh_token(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """Obtain a new access token using a refresh token."""
    service = AuthService(db)
    tokens = await service.refresh_token(request.refresh_token)
    return APIResponse(data=tokens)


@router.post("/logout", response_model=APIResponse[None])
async def logout(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Invalidate the current user's refresh token."""
    service = AuthService(db)
    await service.logout(current_user)
    return APIResponse(message="Logged out successfully")


@router.post("/google", response_model=APIResponse[TokenResponse])
async def google_oauth(
    request: GoogleAuthRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Exchange a Google OAuth authorization code for app tokens.
    The frontend exchanges the Google code server-side via Supabase.
    """
    # In production, the code is exchanged via Supabase Auth
    # Here we accept the decoded user info from the frontend (Supabase handles the OAuth flow)
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {request.code}"},
        )
        if response.status_code != 200:
            from app.core.exceptions import AuthError
            raise AuthError("Failed to fetch Google user info")
        user_info = response.json()

    service = AuthService(db)
    tokens = await service.google_oauth_login(user_info)
    return APIResponse(data=tokens, message="Google login successful")


@router.get("/me", response_model=APIResponse[UserResponse])
async def get_current_user_info(current_user: CurrentUser):
    """Return the currently authenticated user's info."""
    return APIResponse(data=UserResponse.model_validate(current_user))


@router.put("/password", response_model=APIResponse[None])
async def change_password(
    request: PasswordChangeRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Change the current user's password."""
    service = UserService(db)
    await service.change_password(
        user=current_user,
        current_password=request.current_password,
        new_password=request.new_password,
    )
    return APIResponse(message="Password changed successfully")
