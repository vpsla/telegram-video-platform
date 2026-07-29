"""
Video service.

Business logic layer between handlers and VideoRepository. The single
most important rule from the spec lives here: when a user watches a
video, the bot NEVER re-uploads — it calls `bot.copy_message()` against
the stored (channel_id, message_id), and only then records a view.
"""

from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.types import Message

from app.database.models.video import Video
from app.database.repositories.series_repository import SeriesRepository
from app.database.repositories.video_repository import VideoRepository
from app.database.repositories.view_repository import ViewRepository

logger = logging.getLogger(__name__)


class VideoNotFoundError(Exception):
    pass


class VideoService:
    def __init__(
        self,
        video_repo: VideoRepository,
        series_repo: SeriesRepository,
        view_repo: ViewRepository | None = None,
    ) -> None:
        self._video_repo = video_repo
        self._series_repo = series_repo
        self._view_repo = view_repo

    async def register_video(
        self,
        *,
        channel_id: int,
        message_id: int,
        title: str,
        description: str | None = None,
        thumbnail_file_id: str | None = None,
        duration_seconds: int | None = None,
        file_size_bytes: int | None = None,
        category_id: int | None = None,
    ) -> Video:
        """Register a video that has already been uploaded to the storage
        channel. Does not touch Telegram — purely a metadata write."""
        existing = await self._video_repo.get_by_channel_message(channel_id, message_id)
        if existing is not None:
            logger.warning(
                "Video already registered for channel_id=%s message_id=%s (video_id=%s)",
                channel_id,
                message_id,
                existing.id,
            )
            return existing

        return await self._video_repo.create(
            channel_id=channel_id,
            message_id=message_id,
            title=title,
            description=description,
            thumbnail_file_id=thumbnail_file_id,
            duration_seconds=duration_seconds,
            file_size_bytes=file_size_bytes,
            category_id=category_id,
        )

    async def attach_to_series(
        self,
        *,
        video_id: int,
        series_id: int,
        episode_number: int,
        title_override: str | None = None,
    ) -> None:
        existing = await self._video_repo.get_episode_by_video_id(video_id)
        if existing is not None:
            raise ValueError(f"Video {video_id} is already attached as an episode")

        await self._video_repo.attach_as_episode(
            video_id=video_id,
            series_id=series_id,
            episode_number=episode_number,
            title_override=title_override,
        )
        await self._series_repo.increment_episode_count(series_id, delta=1)

    async def send_video_to_user(
        self,
        *,
        bot: Bot,
        chat_id: int,
        video_id: int,
        viewer_user_id: int | None = None,
    ) -> Message:
        """Deliver a video to a user via copy_message and record the view.

        `viewer_user_id` is the internal User.id (not telegram_id) of the
        watching user, used to attribute the view for "Top người xem"
        statistics; pass None for anonymous/unauthenticated contexts.

        Raises VideoNotFoundError if the video doesn't exist or is hidden.
        Any Telegram API error (e.g. the source message was deleted from
        the channel) propagates to the caller — the handler is
        responsible for showing a user-facing error in that case.
        """
        video = await self._video_repo.get_by_id(video_id)
        if video is None or video.is_hidden:
            raise VideoNotFoundError(f"Video {video_id} not found or hidden")

        sent_message = await bot.copy_message(
            chat_id=chat_id,
            from_chat_id=video.channel_id,
            message_id=video.message_id,
        )

        await self._video_repo.increment_view_count(video_id, delta=1)

        if self._view_repo is not None:
            await self._view_repo.record(video_id=video_id, user_id=viewer_user_id)

        episode = await self._video_repo.get_episode_by_video_id(video_id)
        if episode is not None:
            await self._series_repo.increment_views(episode.series_id, delta=1)

        return sent_message
