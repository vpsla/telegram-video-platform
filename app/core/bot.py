"""
Bot and Dispatcher factories.

Kept separate from app wiring (main.py) so that tests and scripts can
import a configured Bot/Dispatcher without booting the full FastAPI app.
"""

from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.config.settings import AppSettings
from app.middlewares.database import DatabaseMiddleware
from app.middlewares.user import UserMiddleware


def create_bot(settings: AppSettings) -> Bot:
    """Create a configured aiogram Bot instance."""
    return Bot(
        token=settings.telegram.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher(settings: AppSettings, session_factory: async_sessionmaker) -> Dispatcher:
    """Create the Dispatcher with FSM storage and core middlewares wired.

    Middleware order matters: DatabaseMiddleware must run first so that
    UserMiddleware (and every handler after it) can rely on
    data["session"] already being present. Registered as outer
    middlewares so they also wrap update types beyond plain messages
    (callback queries, etc.) via Dispatcher's update-level pipeline.

    Phase 1 uses in-memory FSM storage. This will be swapped for
    RedisStorage once Redis is enabled (see app/config/settings.py
    RedisSettings.enabled), without changing any handler code.
    """
    storage = MemoryStorage()
    dispatcher = Dispatcher(storage=storage)
    dispatcher["settings"] = settings

    dispatcher.update.outer_middleware(DatabaseMiddleware(session_factory))
    dispatcher.update.outer_middleware(UserMiddleware(settings))

    return dispatcher
