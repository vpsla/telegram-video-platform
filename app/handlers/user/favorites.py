"""Favorites ("Yêu thích") handler — list series the user follows."""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User
from app.database.repositories.favorite_repository import FavoriteRepository
from app.keyboards.user import series_list_keyboard

logger = logging.getLogger(__name__)

router = Router(name="favorites")

_PAGE_SIZE = 8


@router.callback_query(F.data.startswith("favorites:list:"))
async def show_favorites(callback: CallbackQuery, session: AsyncSession, user: User) -> None:
    offset = int(callback.data.split(":")[-1]) if callback.data else 0
    favorite_repo = FavoriteRepository(session)
    favorites = await favorite_repo.list_for_user(user.id, offset=offset, limit=_PAGE_SIZE)
    series_list = [f.series for f in favorites]

    text = (
        "❤️ <b>Series đang theo dõi</b>"
        if series_list
        else "❤️ <b>Series đang theo dõi</b>\n\nBạn chưa theo dõi series nào."
    )
    keyboard = series_list_keyboard(
        series_list, offset=offset, limit=_PAGE_SIZE, callback_prefix="favorites:list"
    )
    if callback.message is not None:
        await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()
