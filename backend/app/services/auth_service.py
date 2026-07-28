"""
Auth service — registration, login, token management, Google OAuth.
All business logic lives here. Routes only call services.
"""
import hashlib
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthError, ValidationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.models.user import User, UserRole
from app.repositories.user_repository import ProfileRepository, UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.user_repo = UserRepository(db)
        self.profile_repo = ProfileRepository(db)

    async def register(self, request: RegisterRequest) -> TokenResponse:
        """Register a new user with email and password."""
        # Check for duplicate email
        if await self.user_repo.email_exists(request.email.lower()):
            raise ValidationError("An account with this email already exists")

        # Create user
        user = await self.user_repo.create(
            email=request.email.lower(),
            hashed_password=hash_password(request.password),
            role=UserRole.student,
            is_active=True,
            is_email_verified=False,
        )

        # Create empty profile
        await self.profile_repo.create(
            user_id=user.id,
            full_name=request.full_name or "",
        )

        # Issue tokens
        return self._issue_tokens(user)

    async def login(self, request: LoginRequest) -> TokenResponse:
        """Authenticate with email and password."""
        user = await self.user_repo.get_by_email(request.email.lower())

        # Generic error — no user enumeration
        if not user or not user.hashed_password:
            raise AuthError("Invalid email or password")

        if not verify_password(request.password, user.hashed_password):
            raise AuthError("Invalid email or password")

        if not user.is_active:
            raise AuthError("Account is deactivated. Contact support.")

        return self._issue_tokens(user)

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Issue a new access token using a valid refresh token."""
        from jose import JWTError
        from app.core.security import decode_token

        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise AuthError("Invalid token type")

            user_id = payload.get("sub")
            if not user_id:
                raise AuthError("Invalid token")

        except JWTError:
            raise AuthError("Invalid or expired refresh token")

        user = await self.user_repo.get_by_id(UUID(user_id))
        if not user or not user.is_active:
            raise AuthError("User not found or deactivated")

        # Validate token hash matches stored hash (rotation check)
        token_hash = self._hash_token(refresh_token)
        if user.refresh_token_hash and user.refresh_token_hash != token_hash:
            raise AuthError("Refresh token has been rotated. Please login again.")

        return self._issue_tokens(user)

    async def logout(self, user: User) -> None:
        """Invalidate the user's refresh token."""
        await self.user_repo.update(user, refresh_token_hash=None)

    async def google_oauth_login(self, google_user_info: dict) -> TokenResponse:
        """
        Handle Google OAuth login.
        Creates account on first login, links on subsequent logins.
        """
        google_id = google_user_info["sub"]
        email = google_user_info["email"].lower()
        full_name = google_user_info.get("name", "")
        avatar_url = google_user_info.get("picture", "")

        # Check if user exists by Google ID
        user = await self.user_repo.get_by_google_id(google_id)

        if not user:
            # Check if email already registered (link accounts)
            user = await self.user_repo.get_by_email(email)

            if user:
                # Link Google ID to existing account
                user = await self.user_repo.update(
                    user, google_id=google_id, is_email_verified=True
                )
            else:
                # Create new account
                user = await self.user_repo.create(
                    email=email,
                    hashed_password=None,
                    google_id=google_id,
                    role=UserRole.student,
                    is_active=True,
                    is_email_verified=True,
                )
                await self.profile_repo.create(
                    user_id=user.id,
                    full_name=full_name,
                    avatar_url=avatar_url,
                )

        return self._issue_tokens(user)

    def _issue_tokens(self, user: User) -> TokenResponse:
        """Create access + refresh token pair and store refresh token hash."""
        access_token = create_access_token(
            subject=str(user.id),
            role=user.role.value if hasattr(user.role, "value") else user.role,
        )
        refresh_token = create_refresh_token(subject=str(user.id))

        # Fire-and-forget: store refresh token hash (not awaited in sync context)
        # Will be committed by the session in the route handler
        user.refresh_token_hash = self._hash_token(refresh_token)
        self.db.add(user)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()
