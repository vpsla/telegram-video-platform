from __future__ import annotations

from app.config.settings import AppSettings
from app.database.engine import create_engine


async def test_create_engine_uses_asyncpg_driver(settings: AppSettings) -> None:
    engine = create_engine(settings)
    try:
        assert engine.dialect.driver == "asyncpg"
    finally:
        await engine.dispose()


async def test_create_engine_respects_pool_settings(settings: AppSettings) -> None:
    engine = create_engine(settings)
    try:
        assert engine.pool.size() == settings.database.pool_size
    finally:
        await engine.dispose()
