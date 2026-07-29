"""Generic InlineKeyboard builders shared across admin and user flows."""

from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def confirm_cancel_keyboard(
    *, confirm_data: str, cancel_data: str = "admin:cancel"
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Xác nhận", callback_data=confirm_data)
    builder.button(text="❌ Hủy", callback_data=cancel_data)
    builder.adjust(2)
    return builder.as_markup()


def pagination_keyboard(
    *, callback_prefix: str, offset: int, limit: int, has_more: bool
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if offset > 0:
        prev_offset = max(0, offset - limit)
        builder.button(text="⬅️ Trước", callback_data=f"{callback_prefix}:{prev_offset}")
    if has_more:
        builder.button(text="Sau ➡️", callback_data=f"{callback_prefix}:{offset + limit}")
    builder.adjust(2)
    return builder.as_markup()
