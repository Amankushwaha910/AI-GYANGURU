"""
Async SQLAlchemy database engine and session factory.
Configured for Supabase's PgBouncer transaction pooler (port 6543).

Key constraints:
  - statement_cache_size=0  → PgBouncer transaction mode rejects prepared stmts
  - NullPool                → Let PgBouncer manage connection pooling
  - Lazy engine init        → Engine is created inside the running uvicorn event
                              loop, avoiding greenlet/asyncio conflicts that occur
                              when the engine is built at module import time.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.core.config import settings

# ── Lazy engine singleton ─────────────────────────────────────────────────────
# Engine is NOT created at import time.  The first call to get_engine() builds
# it inside the already-running uvicorn event loop, which avoids the greenlet
# bridging timeout seen when SQLAlchemy initialises asyncpg outside an event loop.

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Return (creating if necessary) the shared async engine."""
    global _engine, _session_factory
    if _engine is None:
        _engine = create_async_engine(
            settings.database_url,
            poolclass=NullPool,                        # PgBouncer manages the pool
            echo=settings.app_debug,                   # SQL logging in debug mode
            connect_args={"statement_cache_size": 0},  # Required for PgBouncer tx mode
        )
        _session_factory = async_sessionmaker(
            _engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return (creating if necessary) the shared session factory."""
    get_engine()                  # ensures _session_factory is set
    assert _session_factory is not None
    return _session_factory

 
# ── AsyncSessionLocal alias ───────────────────────────────────────────────────
# Used by background tasks (e.g. file_service._extract_text_background) that
# need to open their own sessions outside the request/response cycle.
# Calling AsyncSessionLocal() returns a new AsyncSession context manager.
class _AsyncSessionLocalProxy:
    """Proxy that lazily resolves the session factory on first call.

    Supports two usage patterns used in background tasks:

        # pattern 1 — direct callable returning a context manager
        async with AsyncSessionLocal() as session: ...

        # pattern 2 — direct context manager (legacy usage)
        async with AsyncSessionLocal as session: ...
    """
    def __call__(self):
        """Return a new AsyncSession context manager."""
        return get_session_factory()()

    async def __aenter__(self):
        # support: async with AsyncSessionLocal as session
        self._session = get_session_factory()()
        return await self._session.__aenter__()

    async def __aexit__(self, *args):
        return await self._session.__aexit__(*args)


AsyncSessionLocal = _AsyncSessionLocalProxy()


# ── Convenience alias used by Alembic and tests ───────────────────────────────
# Accessing this property triggers lazy init — fine for scripts that run their
# own event loop.  In uvicorn, get_db() calls get_session_factory() instead.
@property
def engine() -> AsyncEngine:          # noqa: F811 – module-level property trick
    return get_engine()


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


# ── FastAPI dependency ────────────────────────────────────────────────────────

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency — one session per request.
    Commits on success, rolls back on any exception.
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
