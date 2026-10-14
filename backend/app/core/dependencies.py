"""
FastAPI dependency injection: current user extraction, role guards.
"""
from typing import Annotated, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)


async def _decode_user_id(
    credentials: Optional[HTTPAuthorizationCredentials],
) -> str:
    """Decode JWT and return user_id string. Raises 401 on failure."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise credentials_exception

    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise credentials_exception
        user_id = payload.get("sub")
        if not isinstance(user_id, str):
            raise credentials_exception
        UUID(user_id)
        return user_id
    except (JWTError, ValueError, TypeError, AttributeError):
        raise credentials_exception


async def get_authenticated_user_id(
    credentials: Annotated[
        Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)
    ],
) -> str:
    """Validate bearer credentials before any database dependency is opened."""
    return await _decode_user_id(credentials)


async def get_current_user(
    user_id: Annotated[str, Depends(get_authenticated_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Extract and validate the current user from the Authorization header.
    Loads user WITH profile (needed for /auth/me, profile page, dashboard greeting).
    Returns the ORM User object or raises 401.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    repo = UserRepository(db)
    user = await repo.get_with_profile(UUID(user_id))

    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )
    return user


async def get_current_user_fast(
    user_id: Annotated[str, Depends(get_authenticated_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Lightweight variant — loads user WITHOUT the profile join.
    Use this on high-frequency endpoints (file polling, list queries, AI generation)
    where the profile data is not needed, to save one DB round-trip per request.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    repo = UserRepository(db)
    user = await repo.get_by_id(UUID(user_id))

    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )
    return user


# ── Role Guards ───────────────────────────────────────────────────────────────

def require_role(*roles: UserRole):
    """
    Factory that returns a dependency checking the current user has one of the given roles.
    Usage: Depends(require_role(UserRole.admin, UserRole.teacher))
    """
    async def role_checker(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {[r.value for r in roles]}",
            )
        return current_user

    return role_checker


# ── Type Aliases ──────────────────────────────────────────────────────────────

CurrentUser = Annotated[User, Depends(get_current_user)]
# Fast variant — no profile join; use for high-frequency endpoints
CurrentUserFast = Annotated[User, Depends(get_current_user_fast)]
AdminUser = Annotated[User, Depends(require_role(UserRole.admin))]
TeacherUser = Annotated[User, Depends(require_role(UserRole.teacher, UserRole.admin))]
