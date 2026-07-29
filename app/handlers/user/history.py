"""History ("Lịch sử") and continue-watching ("Tiếp tục xem") handlers."""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User
from app.database.repositories.history_repository import HistoryRepository
from app.database.repositories.watch_progress_repository import WatchProgressRepository
from app.keyboards.user import video_list_keyboard
from app.services.history_service import HistoryService

logger = logging.getLogger(__name__)

router = Router(name="history")

_PAGE_SIZE = 8


def _build_service(session: AsyncSession) -> HistoryService:
    return HistoryService(HistoryRepository(session), WatchProgressRepository(session))


@router.callback_query(F.data.startswith("history:list:"))
async def show_history(callback: CallbackQuery, session: AsyncSession, user: User) -> None:
    offset = int(callback.data.split(":")[-1]) if callback.data else 0
    service = _build_service(session)
    entries = await service.get_history(user.id, offset=offset, limit=_PAGE_SIZE)
    videos = [entry.video for entry in entries]

    text = "🕘 <b>Lịch sử xem</b>" if videos else "🕘 <b>Lịch sử xem</b>\n\nChưa có video nào."
    keyboard = video_list_keyboard(
        videos, offset=offset, limit=_PAGE_SIZE, callback_prefix="history:list"
    )
    if callback.message is not None:
        await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "continue:list")
async def show_continue_watching(
    callback: CallbackQuery, session: AsyncSession, user: User
) -> None:
    service = _build_service(session)
    videos = await service.get_continue_watching_videos(user.id, limit=_PAGE_SIZE)

    text = (
        "▶️ <b>Tiếp tục xem</b>"
        if videos
        else "▶️ <b>Tiếp tục xem</b>\n\nBạn chưa xem video nào đang dở."
    )
    keyboard = video_list_keyboard(
        videos, offset=0, limit=_PAGE_SIZE, callback_prefix="continue:page"
    )
    if callback.message is not None:
        await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()
