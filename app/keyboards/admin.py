"""Reusable InlineKeyboard builders for the admin panel."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.database.models.category import Category
from app.keyboards.common import confirm_cancel_keyboard, pagination_keyboard

__all__ = [
    "admin_main_menu_keyboard",
    "category_choice_keyboard",
    "confirm_cancel_keyboard",
    "pagination_keyboard",
]


def category_choice_keyboard(
    categories: list[Category], *, callback_prefix: str
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for category in categories:
        label = f"{category.icon_emoji or ''} {category.name}".strip()
        builder.button(text=label, callback_data=f"{callback_prefix}:{category.id}")
    builder.adjust(2)
    return builder.as_markup()


def admin_main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🎬 Thêm video", callback_data="admin:add_video"))
    builder.row(
        InlineKeyboardButton(text="📚 Tạo playlist/series", callback_data="admin:create_series")
    )
    builder.row(InlineKeyboardButton(text="🏷️ Quản lý thể loại", callback_data="admin:categories"))
    builder.row(InlineKeyboardButton(text="👥 Quản lý user", callback_data="admin:users"))
    builder.row(InlineKeyboardButton(text="📢 Broadcast", callback_data="admin:broadcast"))
    builder.row(InlineKeyboardButton(text="📊 Dashboard", callback_data="admin:dashboard"))
    builder.row(InlineKeyboardButton(text="📤 Export dữ liệu", callback_data="admin:export"))
    return builder.as_markup()
