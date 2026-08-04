"""
Handler for data sent back from the Telegram Mini App via
`Telegram.WebApp.sendData()`. This is how the Mini App (a static
frontend with no ability to call bot.copy_message itself) asks the bot
to actually deliver a video — the Mini App can only browse/search;
final delivery always goes through the same PlaybackService used by
the native InlineKeyboard flow, so history/stats stay consistent
regardless of which UI triggered the watch.
"""

from __future__ import annotations

import json
import logging

from aiogram import Bot, Router
from aiogram.types import Message
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

router = Router(name="web_app_data")


@router.message(lambda m: m.web_app_data is not None)
async def handle_web_app_data(
    message: Message,
    session: AsyncSession,
    user: User,
    bot: Bot,
) -> None:
    try:
        payload = json.loads(message.web_app_data.data)
    except (json.JSONDecodeError, AttributeError):
        logger.warning("Invalid web_app_data payload from user_id=%s", user.id)
        return

    action = payload.get("action")
    if action != "watch":
        logger.warning("Unknown Mini App action: %s", action)
        return

    video_id = payload.get("video_id")
    if not isinstance(video_id, int):
        await message.answer("⚠️ Yêu cầu không hợp lệ từ Mini App.")
        return

    video_service = VideoService(VideoRepository(session), SeriesRepository(session))
    history_service = HistoryService(HistoryRepository(session), WatchProgressRepository(session))
    playback_service = PlaybackService(video_service, history_service)

    try:
        await playback_service.play_video(
            bot=bot,
            chat_id=message.chat.id,
            user_id=user.id,
            video_id=video_id,
        )
    except VideoNotFoundError:
        await message.answer("⚠️ Video không tồn tại hoặc đã bị ẩn.")
    except Exception:
        logger.exception("Failed to deliver video_id=%s from Mini App", video_id)
        await message.answer("⚠️ Có lỗi xảy ra khi gửi video. Vui lòng thử lại.")
