"""
Playback service.

Every time a video is actually delivered to a user, three things must
happen together: the Telegram copy_message call, the view/stats
counters (VideoService), and the history log (HistoryService). Coupling
them here — rather than relying on every handler to call both services
in the right order — means a new "watch video" entry point (browse,
search results, continue-watching, favorites) can never forget one.
"""

from __future__ import annotations

from aiogram import Bot
from aiogram.types import Message

from app.services.history_service import HistoryService
from app.services.video_service import VideoService


class PlaybackService:
    def __init__(self, video_service: VideoService, history_service: HistoryService) -> None:
        self._video_service = video_service
        self._history_service = history_service

    async def play_video(
        self,
        *,
        bot: Bot,
        chat_id: int,
        user_id: int,
        video_id: int,
    ) -> Message:
        """Deliver `video_id` to `chat_id` and record the watch event.

        Propagates VideoNotFoundError from VideoService unchanged — the
        caller (handler) decides how to present that to the user.
        """
        sent_message = await self._video_service.send_video_to_user(
            bot=bot,
            chat_id=chat_id,
            video_id=video_id,
            viewer_user_id=user_id,
        )
        await self._history_service.record_watch_start(user_id=user_id, video_id=video_id)
        return sent_message
