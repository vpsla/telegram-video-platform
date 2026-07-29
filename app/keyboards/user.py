"""Reusable InlineKeyboard builders for end-user-facing flows."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.database.models.category import Category
from app.database.models.episode import Episode
from app.database.models.series import Series
from app.database.models.video import Video


def home_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🆕 Video mới", callback_data="browse:newest:0"),
        InlineKeyboardButton(text="🔥 Nổi bật", callback_data="browse:featured:0"),
    )
    builder.row(
        InlineKeyboardButton(text="🏷️ Thể loại", callback_data="browse:categories"),
        InlineKeyboardButton(text="🔎 Tìm kiếm", callback_data="search:prompt"),
    )
    builder.row(
        InlineKeyboardButton(text="▶️ Tiếp tục xem", callback_data="continue:list"),
        InlineKeyboardButton(text="🕘 Lịch sử", callback_data="history:list:0"),
    )
    builder.row(
        InlineKeyboardButton(text="❤️ Yêu thích", callback_data="favorites:list:0"),
        InlineKeyboardButton(text="👤 Tài khoản", callback_data="account:info"),
    )
    return builder.as_markup()


def series_list_keyboard(
    series_list: list[Series], *, offset: int, limit: int, callback_prefix: str = "browse:page"
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for series in series_list:
        builder.row(
            InlineKeyboardButton(
                text=f"📖 {series.title}", callback_data=f"series:view:{series.id}"
            )
        )
    nav_row = []
    if offset > 0:
        nav_row.append(
            InlineKeyboardButton(
                text="⬅️ Trước", callback_data=f"{callback_prefix}:{max(0, offset - limit)}"
            )
        )
    if len(series_list) == limit:
        nav_row.append(
            InlineKeyboardButton(text="Sau ➡️", callback_data=f"{callback_prefix}:{offset + limit}")
        )
    if nav_row:
        builder.row(*nav_row)
    builder.row(InlineKeyboardButton(text="🏠 Trang chủ", callback_data="home:menu"))
    return builder.as_markup()


def category_list_keyboard(categories: list[Category]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for category in categories:
        label = f"{category.icon_emoji or ''} {category.name}".strip()
        builder.button(text=label, callback_data=f"browse:category:{category.id}:0")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="🏠 Trang chủ", callback_data="home:menu"))
    return builder.as_markup()


def series_detail_keyboard(
    series: Series, episodes: list[Episode], *, is_following: bool
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for episode in episodes:
        label = episode.title_override or f"Tập {episode.episode_number}"
        builder.row(
            InlineKeyboardButton(text=f"▶️ {label}", callback_data=f"watch:video:{episode.video_id}")
        )
    follow_label = "💔 Bỏ theo dõi" if is_following else "❤️ Theo dõi"
    builder.row(InlineKeyboardButton(text=follow_label, callback_data=f"series:follow:{series.id}"))
    builder.row(InlineKeyboardButton(text="🏠 Trang chủ", callback_data="home:menu"))
    return builder.as_markup()


def video_list_keyboard(
    videos: list[Video], *, offset: int, limit: int, callback_prefix: str
) -> InlineKeyboardMarkup:
    """Generic paginated list of standalone videos — used for
    'Video lẻ mới', history, continue-watching, favorites, search."""
    builder = InlineKeyboardBuilder()
    for video in videos:
        builder.row(
            InlineKeyboardButton(text=f"▶️ {video.title}", callback_data=f"watch:video:{video.id}")
        )
    nav_row = []
    if offset > 0:
        nav_row.append(
            InlineKeyboardButton(
                text="⬅️ Trước", callback_data=f"{callback_prefix}:{max(0, offset - limit)}"
            )
        )
    if len(videos) == limit:
        nav_row.append(
            InlineKeyboardButton(text="Sau ➡️", callback_data=f"{callback_prefix}:{offset + limit}")
        )
    if nav_row:
        builder.row(*nav_row)
    builder.row(InlineKeyboardButton(text="🏠 Trang chủ", callback_data="home:menu"))
    return builder.as_markup()
