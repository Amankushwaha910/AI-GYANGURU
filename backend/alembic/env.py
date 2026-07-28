"""
Alembic environment configuration.
Uses async SQLAlchemy engine with auto-discovered models.
"""
import asyncio
from logging.config import fileConfig
from typing import Optional

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Import settings and Base so Alembic can discover all models
from app.core.config import settings
from app.core.database import Base

# Import all models to register them with Base.metadata
import app.models  # noqa: F401

config = context.config

# Override sqlalchemy.url from environment.
# configparser uses % as an interpolation character, so literal % signs in the
# URL (e.g. URL-encoded passwords like %40) must be doubled to %% before being
# stored in the config, otherwise set_main_option raises a ValueError.
_db_url = settings.database_url.replace("%", "%%")
config.set_main_option("sqlalchemy.url", _db_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in async mode."""
    # statement_cache_size=0 is required for Supabase's PgBouncer transaction
    # pooler (port 6543), which does not support asyncpg prepared statements.
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args={"statement_cache_size": 0},
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
