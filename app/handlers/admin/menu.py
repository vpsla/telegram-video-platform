"""
/admin command handler — entry point into the admin panel.

Gated by IsAdminFilter at the router level (see app/routers/admin/__init__.py),
so reaching this handler already guarantees `user.is_admin is True`.
"""

from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.keyboards.admin import admin_main_menu_keyboard

logger = logging.getLogger(__name__)

router = Router(name="admin_menu")


@router.message(Command("admin"))
async def handle_admin_menu(message: Message) -> None:
    await message.answer(
        "🛠 <b>Bảng điều khiển Admin</b>\n\nChọn một chức năng bên dưới:",
        reply_markup=admin_main_menu_keyboard(),
    )


@router.callback_query(lambda c: c.data == "admin:menu")
async def handle_back_to_menu(callback: CallbackQuery) -> None:
    if callback.message is not None:
        await callback.message.edit_text(
            "🛠 <b>Bảng điều khiển Admin</b>\n\nChọn một chức năng bên dưới:",
            reply_markup=admin_main_menu_keyboard(),
        )
    await callback.answer()


@router.callback_query(lambda c: c.data == "admin:cancel")
async def handle_cancel(callback: CallbackQuery) -> None:
    if callback.message is not None:
        await callback.message.edit_text("❌ Đã hủy thao tác.")
    await callback.answer()
