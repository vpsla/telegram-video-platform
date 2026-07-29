"""Browsing handlers: Video mới, Video nổi bật, Thể loại, chi tiết series."""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User
from app.database.repositories.category_repository import CategoryRepository
from app.database.repositories.favorite_repository import FavoriteRepository
from app.database.repositories.series_repository import SeriesRepository
from app.database.repositories.video_repository import VideoRepository
from app.keyboards.user import (
    category_list_keyboard,
    series_detail_keyboard,
    series_list_keyboard,
)
from app.services.favorite_service import FavoriteService

logger = logging.getLogger(__name__)

router = Router(name="browse")

_PAGE_SIZE = 8


@router.callback_query(F.data.startswith("browse:newest:"))
async def show_newest(callback: CallbackQuery, session: AsyncSession) -> None:
    offset = int(callback.data.split(":")[-1]) if callback.data else 0
    series_repo = SeriesRepository(session)
    series_list = await series_repo.list_newest(offset=offset, limit=_PAGE_SIZE)

    text = "🆕 <b>Video mới</b>" if series_list else "🆕 <b>Video mới</b>\n\nChưa có nội dung nào."
    keyboard = series_list_keyboard(
        series_list, offset=offset, limit=_PAGE_SIZE, callback_prefix="browse:newest"
    )
    if callback.message is not None:
        await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("browse:featured:"))
async def show_featured(callback: CallbackQuery, session: AsyncSession) -> None:
    offset = int(callback.data.split(":")[-1]) if callback.data else 0
    series_repo = SeriesRepository(session)
    series_list = await series_repo.list_featured(offset=offset, limit=_PAGE_SIZE)

    text = (
        "🔥 <b>Video nổi bật</b>"
        if series_list
        else "🔥 <b>Video nổi bật</b>\n\nChưa có nội dung nào."
    )
    keyboard = series_list_keyboard(
        series_list, offset=offset, limit=_PAGE_SIZE, callback_prefix="browse:featured"
    )
    if callback.message is not None:
        await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "browse:categories")
async def show_categories(callback: CallbackQuery, session: AsyncSession) -> None:
    category_repo = CategoryRepository(session)
    categories = await category_repo.list_active()

    text = "🏷️ <b>Chọn thể loại</b>" if categories else "🏷️ Chưa có thể loại nào."
    if callback.message is not None:
        await callback.message.edit_text(text, reply_markup=category_list_keyboard(categories))
    await callback.answer()


@router.callback_query(F.data.startswith("browse:category:"))
async def show_series_by_category(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.data is None:
        return
    parts = callback.data.split(":")
    category_id, offset = int(parts[2]), int(parts[3])

    series_repo = SeriesRepository(session)
    series_list = await series_repo.list_by_category(category_id, offset=offset, limit=_PAGE_SIZE)

    text = "📚 <b>Series trong thể loại này</b>" if series_list else "📚 Chưa có series nào."
    keyboard = series_list_keyboard(
        series_list,
        offset=offset,
        limit=_PAGE_SIZE,
        callback_prefix=f"browse:category:{category_id}",
    )
    if callback.message is not None:
        await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("series:view:"))
async def show_series_detail(callback: CallbackQuery, session: AsyncSession, user: User) -> None:
    if callback.data is None:
        return
    series_id = int(callback.data.split(":")[-1])

    series_repo = SeriesRepository(session)
    video_repo = VideoRepository(session)
    favorite_repo = FavoriteRepository(session)

    series = await series_repo.get_by_id(series_id)
    if series is None:
        await callback.answer("Không tìm thấy series.", show_alert=True)
        return

    episodes = await video_repo.list_episodes_for_series(series_id)
    is_following = await favorite_repo.is_following(user.id, series_id)

    status = "✅ Hoàn thành" if series.is_completed else "🔄 Đang tiến hành"
    text = (
        f"📖 <b>{series.title}</b>\n"
        f"✍️ Tác giả: {series.author or 'Không rõ'}\n"
        f"📊 Trạng thái: {status}\n"
        f"👁️ Lượt xem: {series.total_views}\n"
        f"❤️ Người theo dõi: {series.follower_count}\n"
        f"🎬 Số tập: {series.episode_count}\n\n"
        f"{series.description or ''}"
    )
    keyboard = series_detail_keyboard(series, episodes, is_following=is_following)
    if callback.message is not None:
        await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("series:follow:"))
async def toggle_follow_series(callback: CallbackQuery, session: AsyncSession, user: User) -> None:
    if callback.data is None:
        return
    series_id = int(callback.data.split(":")[-1])

    favorite_repo = FavoriteRepository(session)
    series_repo = SeriesRepository(session)
    favorite_service = FavoriteService(favorite_repo, series_repo)

    now_following = await favorite_service.toggle(user_id=user.id, series_id=series_id)
    await callback.answer("❤️ Đã theo dõi!" if now_following else "💔 Đã bỏ theo dõi.")

    # Refresh the detail view so the follow button label stays in sync.
    video_repo = VideoRepository(session)
    series = await series_repo.get_by_id(series_id)
    if series is None or callback.message is None:
        return
    episodes = await video_repo.list_episodes_for_series(series_id)
    keyboard = series_detail_keyboard(series, episodes, is_following=now_following)
    await callback.message.edit_reply_markup(reply_markup=keyboard)
