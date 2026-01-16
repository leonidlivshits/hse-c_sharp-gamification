"""
migrations/env.py
DESCRIPTION: Alembic env for async SQLAlchemy usage.

Behavior:
- If environment variable DATABASE_URL is set, it will be used.
- Otherwise it will try to read POSTGRES_* components and construct the URL similarly
  to app.core.config.get_database_url().
- Uses app.db.session.Base.metadata (so make sure models are imported in app.models.__init__).

This file also makes sure the project root is on sys.path so `import app` works
when running alembic from inside a container.
"""
import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

# --- ensure project root is on sys.path so "import app" resolves ---
# migrations/env.py lives in <project_root>/migrations/env.py
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# this is the Alembic Config object, which provides access to the values within the .ini file
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import app metadata after sys.path fix
try:
    # ensure models package imports so metadata is populated
    import app.models  # noqa: F401
    from app.db.session import Base  # type: ignore
except Exception as exc:
    # Provide a helpful message if import fails
    raise RuntimeError(
        "Failed to import application package 'app'. Make sure the project root "
        "is on PYTHONPATH and that 'app' is a proper Python package (has __init__.py). "
        f"Original error: {exc}"
    ) from exc

target_metadata = Base.metadata


def construct_db_url_from_env() -> str:
    """
    Build DATABASE_URL from POSTGRES_* env variables (same logic as app.core.config).
    """
    env_db_url = os.environ.get("DATABASE_URL")
    if env_db_url:
        return env_db_url

    user = os.environ.get("POSTGRES_USER", "postgres")
    pw = os.environ.get("POSTGRES_PASSWORD", "postgres")
    host = os.environ.get("POSTGRES_HOST", "postgres")
    port = os.environ.get("POSTGRES_PORT", "5432")
    db = os.environ.get("POSTGRES_DB", "app_db")
    return f"postgresql+asyncpg://{user}:{pw}@{host}:{port}/{db}"


def run_migrations_offline():
    """Run migrations in 'offline' mode (generate SQL)."""
    url = construct_db_url_from_env()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    """Run migrations in 'online' (connected) mode using an async engine."""
    url = construct_db_url_from_env()
    connectable = create_async_engine(url, poolclass=pool.NullPool)

    async with connectable.connect() as connection:
        # run migrations in sync context using run_sync helper
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
