"""
Watch handler: delivers a video to the user via copy_message.

This is the single entry point every "play" button across the bot
routes through (browse, search results, continue-watching, favorites,
history) — always via PlaybackService so view stats and history stay
in sync no matter where the tap originated.
"""

from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User
from app.database.repositories.history_repository import HistoryRepository
from app.database.repositories.series_repository import SeriesRepository
from app.database.repositories.video_repository import VideoRepository
from app.database.repositories.watch_progress_repository import WatchProgressRepository
from app.services.history_service import HistoryService
from app.services.playback_service import PlaybackService
from app.services.video_service import VideoNotFoundError, VideoService

logger = logging.getLogger(__name__)

router = Router(name="watch")


@router.callback_query(F.data.startswith("watch:video:"))
async def watch_video(
    callback: CallbackQuery,
    session: AsyncSession,
    user: User,
    bot: Bot,
) -> None:
    if callback.data is None:
        return
    video_id = int(callback.data.split(":")[-1])

    video_service = VideoService(VideoRepository(session), SeriesRepository(session))
    history_service = HistoryService(HistoryRepository(session), WatchProgressRepository(session))
    playback_service = PlaybackService(video_service, history_service)

    try:
        await playback_service.play_video(
            bot=bot,
            chat_id=callback.message.chat.id if callback.message else user.telegram_id,
            user_id=user.id,
            video_id=video_id,
        )
        await callback.answer("▶️ Đang gửi video...")
    except VideoNotFoundError:
        await callback.answer("⚠️ Video không tồn tại hoặc đã bị ẩn.", show_alert=True)
    except Exception:
        logger.exception("Failed to deliver video_id=%s to user_id=%s", video_id, user.id)
        await callback.answer(
            "⚠️ Có lỗi xảy ra khi gửi video. Vui lòng thử lại sau.", show_alert=True
        )
