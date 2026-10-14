"""
Auth service — registration, login, token management, Google OAuth.
All business logic lives here. Routes only call services.
"""
import hashlib
from time import perf_counter
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.exceptions import AuthError, ValidationError
from app.core.performance import add_timing
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.models.user import User, UserRole
from app.repositories.user_repository import ProfileRepository, UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserResponse


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.user_repo = UserRepository(db)
        self.profile_repo = ProfileRepository(db)

    async def register(self, request: RegisterRequest) -> TokenResponse:
        """Register a new user with email and password."""
        # Check for duplicate email
        phase_started = perf_counter()
        if await self.user_repo.email_exists(request.email.lower()):
            raise ValidationError("An account with this email already exists")
        add_timing("auth_email_check", (perf_counter() - phase_started) * 1000)

        # Create user
        phase_started = perf_counter()
        password_hash = hash_password(request.password)
        add_timing("bcrypt_hash", (perf_counter() - phase_started) * 1000)
        phase_started = perf_counter()
        user = await self.user_repo.create(
            email=request.email.lower(),
            hashed_password=password_hash,
            role=UserRole.student,
            is_active=True,
            is_email_verified=False,
        )
        add_timing("auth_user_create", (perf_counter() - phase_started) * 1000)

        # Create empty profile
        profile = await self.profile_repo.create(
            user_id=user.id,
            full_name=request.full_name or "",
        )
        user.profile = profile

        # Issue tokens
        return self._issue_tokens(user, include_user=True)

    async def login(self, request: LoginRequest) -> TokenResponse:
        """Authenticate with email and password."""
        phase_started = perf_counter()
        user = await self.user_repo.get_by_email(request.email.lower())
        add_timing("auth_user_lookup", (perf_counter() - phase_started) * 1000)

        # Generic error — no user enumeration
        if not user or not user.hashed_password:
            raise AuthError("Invalid email or password")

        phase_started = perf_counter()
        # Password verification is CPU-bound and synchronous. Run it off the
        # event loop so a login does not block unrelated async requests.
        valid_password = await run_in_threadpool(
            verify_password, request.password, user.hashed_password
        )
        add_timing("bcrypt_verify", (perf_counter() - phase_started) * 1000)
        if not valid_password:
            raise AuthError("Invalid email or password")

        if not user.is_active:
            raise AuthError("Account is deactivated. Contact support.")

        return self._issue_tokens(user, include_user=True)

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

        # Validate and atomically rotate the stored hash. A read-then-write here
        # lets two concurrent refresh requests both succeed with incompatible
        # tokens, so the repository applies the previous hash in the UPDATE WHERE.
        previous_hash = user.refresh_token_hash
        token_hash = self._hash_token(refresh_token)
        if previous_hash is not None and previous_hash != token_hash:
            raise AuthError("Refresh token has been rotated. Please login again.")

        access_token = create_access_token(
            subject=str(user.id),
            role=user.role.value if hasattr(user.role, "value") else user.role,
        )
        next_refresh_token = create_refresh_token(subject=str(user.id))
        rotated = await self.user_repo.rotate_refresh_token_hash(
            user.id,
            previous_hash,
            self._hash_token(next_refresh_token),
        )
        if not rotated:
            raise AuthError("Refresh token has been rotated. Please login again.")

        return TokenResponse(
            access_token=access_token,
            refresh_token=next_refresh_token,
            token_type="bearer",
        )

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

    def _issue_tokens(self, user: User, include_user: bool = False) -> TokenResponse:
        """Create access + refresh token pair and store refresh token hash."""
        phase_started = perf_counter()
        access_token = create_access_token(
            subject=str(user.id),
            role=user.role.value if hasattr(user.role, "value") else user.role,
        )
        refresh_token = create_refresh_token(subject=str(user.id))

        # Fire-and-forget: store refresh token hash (not awaited in sync context)
        # Will be committed by the session in the route handler
        user.refresh_token_hash = self._hash_token(refresh_token)
        self.db.add(user)

        tokens = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserResponse.model_validate(user) if include_user else None,
        )
        add_timing("jwt_and_auth_response_model", (perf_counter() - phase_started) * 1000)
        return tokens

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()
