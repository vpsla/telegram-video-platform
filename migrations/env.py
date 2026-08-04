"""
Alembic migration environment.

Uses the same DATABASE_URL / SQLAlchemy settings as the running app
(via app.config.settings) so there is a single source of truth for the
connection string — no duplication between .env and alembic.ini.

Models are registered on Base.metadata as they're added in
app/database/models/*.py (starting Phase 2); autogenerate will pick
them up automatically once they exist.
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import Connection, pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.config.settings import get_settings
<<<<<<< HEAD
from app.database.base import Base
=======
>>>>>>> aa711cf084e31aa3c44790aacdffc3901927f779

# Import all model modules here so Base.metadata is fully populated
# before autogenerate compares it against the live database.
from app.database import models  # noqa: F401
<<<<<<< HEAD
=======
from app.database.base import Base
>>>>>>> aa711cf084e31aa3c44790aacdffc3901927f779

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database.url.get_secret_value())

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (generates SQL without a live DB connection)."""
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


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode using an async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
