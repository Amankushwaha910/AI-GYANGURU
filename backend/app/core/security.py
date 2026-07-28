"""
Security utilities: JWT creation/verification, password hashing, token types.
"""
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


# ── Password Utilities ────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """
    Hash a plaintext password using bcrypt.
    Passwords are truncated to 72 bytes (bcrypt's max) to avoid errors.
    """
    # Encode to UTF-8 and truncate to 72 bytes (bcrypt's hard limit)
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    try:
        password_bytes = plain_password.encode('utf-8')[:72]
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except (ValueError, AttributeError):
        return False


# ── JWT Utilities ─────────────────────────────────────────────────────────────

def create_access_token(
    subject: str,
    role: str = "student",
    extra_claims: Optional[dict] = None,
) -> str:
    """
    Create a short-lived JWT access token.
    Subject is the user's UUID string.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.jwt_access_token_expire_minutes)

    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "type": "access",
        "iat": now,
        "exp": expire,
        "jti": str(uuid.uuid4()),  # JWT ID for revocation tracking
    }

    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(subject: str) -> str:
    """
    Create a long-lived JWT refresh token.
    Used to obtain new access tokens without re-authentication.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.jwt_refresh_token_expire_days)

    payload: dict[str, Any] = {
        "sub": subject,
        "type": "refresh",
        "iat": now,
        "exp": expire,
        "jti": str(uuid.uuid4()),
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT token.
    Raises JWTError if the token is invalid or expired.
    """
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )


def get_token_subject(token: str) -> Optional[str]:
    """Extract the subject (user ID) from a token without raising."""
    try:
        payload = decode_token(token)
        return payload.get("sub")
    except JWTError:
        return None


# ── Hashing Utilities ─────────────────────────────────────────────────────────

def hash_content(content: str) -> str:
    """SHA-256 hash of a string — used for prompt deduplication logging."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
