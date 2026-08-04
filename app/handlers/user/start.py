"""
/start command handler.

By the time this handler runs, DatabaseMiddleware + UserMiddleware have
already opened a DB session and get-or-created the User row -- this
handler only needs to read `user` from the middleware-injected data,
never touch the repository or session directly for registration.
"""

from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.config.settings import AppSettings
from app.database.models.user import User
from app.keyboards.user import home_menu_keyboard

logger = logging.getLogger(__name__)

router = Router(name="start")


@router.message(CommandStart())
async def handle_start(message: Message, user: User, settings: AppSettings) -> None:
    logger.info("Received /start from telegram_id=%s", user.telegram_id)

    greeting = (
        f"👋 Chào mừng trở lại, <b>{user.display_name}</b>!"
        if user.total_watch_seconds > 0
        else "👋 Chào mừng đến với <b>Telegram Video Platform</b>!"
    )

    await message.answer(
        f"{greeting}\n\n"
        "Nền tảng xem video truyện/audio - xem, tìm kiếm, theo dõi bộ truyện yêu thích.",
        reply_markup=home_menu_keyboard(settings.telegram.miniapp_url),
    )
