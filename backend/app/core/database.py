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
from uuid import uuid4

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool

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
        database_url = make_url(settings.database_url)
        engine_options = {"echo": settings.app_debug}
        if settings.database_pool_mode == "session":
            # Supabase session mode (port 5432) pins a server connection for
            # each client connection, so a small application pool can safely
            # reuse asyncpg prepared statements between requests.
            engine_options.update(
                poolclass=AsyncAdaptedQueuePool,
                pool_size=settings.database_pool_size,
                max_overflow=settings.database_max_overflow,
                pool_timeout=settings.database_pool_timeout_seconds,
                pool_recycle=settings.database_pool_recycle_seconds,
                # Per-checkout ping costs a database round trip; aged sockets
                # are recycled and failed connections are invalidated by SQLAlchemy.
                pool_pre_ping=False,
            )
            connect_args = {}
        else:
            # Transaction poolers reuse backend sessions. Disable both caches
            # and use unique names to avoid collisions across client connections.
            database_url = database_url.update_query_dict(
                {"prepared_statement_cache_size": "0"}
            )
            engine_options["poolclass"] = NullPool
            connect_args = {
                "statement_cache_size": 0,
                "prepared_statement_name_func": lambda: f"__asyncpg_{uuid4().hex}__",
            }
        _engine = create_async_engine(
            database_url,
            connect_args=connect_args,
            **engine_options,
        )
        from app.core.performance import (
            finish_failed_query,
            finish_query,
            measure_driver_connect,
            start_query,
        )

        def timed_driver_connect(dialect, connection_record, cargs, cparams):
            # SQLAlchemy documents do_connect as a supported connection override.
            # Calling the same dialect.connect function with the unchanged
            # arguments preserves the default asyncpg path while timing success
            # and failure in the same event context as the request timings.
            return measure_driver_connect(
                lambda: dialect.connect(*cargs, **cparams)
            )

        def before_query(conn, cursor, statement, parameters, context, executemany):
            conn.info["gyanguru_query_started"] = start_query()

        def after_query(conn, cursor, statement, parameters, context, executemany):
            started = conn.info.pop("gyanguru_query_started", None)
            if started is not None:
                finish_query(started, statement)

        def query_error(exception_context):
            # Do not include exception text or bound parameters in diagnostics.
            finish_failed_query(
                getattr(exception_context, "connection", None),
                getattr(exception_context, "statement", None),
            )

        event.listen(_engine.sync_engine, "before_cursor_execute", before_query)
        event.listen(_engine.sync_engine, "after_cursor_execute", after_query)
        event.listen(_engine.sync_engine, "handle_error", query_error)
        event.listen(_engine.sync_engine, "do_connect", timed_driver_connect)
        _session_factory = async_sessionmaker(
            _engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    return _engine


async def dispose_engine() -> None:
    """Close pooled connections cleanly during application shutdown."""
    global _engine, _session_factory
    engine = _engine
    _engine = None
    _session_factory = None
    if engine is not None:
        await engine.dispose()


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
            from app.core.performance import (
                add_timing,
                begin_connection_acquisition,
                finish_connection_acquisition,
            )

            connect_started, acquisition_token = begin_connection_acquisition()
            try:
                await session.connection()
            finally:
                finish_connection_acquisition(connect_started, acquisition_token)
            yield session
            from time import perf_counter

            commit_started = perf_counter()
            try:
                await session.commit()
            finally:
                add_timing("db_commit", (perf_counter() - commit_started) * 1000)
        except Exception:
            from time import perf_counter
            from app.core.performance import add_timing

            rollback_started = perf_counter()
            try:
                await session.rollback()
            finally:
                add_timing("db_rollback", (perf_counter() - rollback_started) * 1000)
            raise
        finally:
            from time import perf_counter
            from app.core.performance import add_timing

            release_started = perf_counter()
            try:
                await session.close()
            finally:
                add_timing("db_release", (perf_counter() - release_started) * 1000)
