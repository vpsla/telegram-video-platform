"""Home menu handler ("Trang chủ") for regular users."""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.config.settings import AppSettings
from app.keyboards.user import home_menu_keyboard

logger = logging.getLogger(__name__)

router = Router(name="home")

_HOME_TEXT = "🏠 <b>Trang chủ</b>\n\nChọn một mục bên dưới để bắt đầu:"


@router.message(Command("menu"))
async def show_home_menu(message: Message, settings: AppSettings) -> None:
    await message.answer(_HOME_TEXT, reply_markup=home_menu_keyboard(settings.telegram.miniapp_url))


@router.callback_query(F.data == "home:menu")
async def back_to_home_menu(callback: CallbackQuery, settings: AppSettings) -> None:
    if callback.message is not None:
        await callback.message.edit_text(
            _HOME_TEXT, reply_markup=home_menu_keyboard(settings.telegram.miniapp_url)
        )
    await callback.answer()
