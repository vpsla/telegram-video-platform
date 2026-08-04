from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.history_repository import HistoryRepository
from app.database.repositories.series_repository import SeriesRepository
from app.database.repositories.user_repository import UserRepository
from app.database.repositories.video_repository import VideoRepository
from app.database.repositories.watch_progress_repository import WatchProgressRepository
from app.services.history_service import HistoryService
from app.services.playback_service import PlaybackService
from app.services.video_service import VideoNotFoundError, VideoService


async def test_play_video_records_history_and_view(db_session: AsyncSession) -> None:
    user_repo = UserRepository(db_session)
    video_repo = VideoRepository(db_session)
    series_repo = SeriesRepository(db_session)
    history_repo = HistoryRepository(db_session)
    progress_repo = WatchProgressRepository(db_session)

    video_service = VideoService(video_repo, series_repo)
    history_service = HistoryService(history_repo, progress_repo)
    playback_service = PlaybackService(video_service, history_service)

    user, _ = await user_repo.get_or_create(telegram_id=1)
    video = await video_service.register_video(channel_id=-100, message_id=1, title="V")

    bot = AsyncMock()
    bot.copy_message = AsyncMock(return_value="sent")

    result = await playback_service.play_video(
        bot=bot, chat_id=user.telegram_id, user_id=user.id, video_id=video.id
    )

    assert result == "sent"
    history = await history_service.get_history(user.id)
    assert len(history) == 1
    assert history[0].video_id == video.id

    reloaded_video = await video_repo.get_by_id(video.id)
    assert reloaded_video is not None
    assert reloaded_video.view_count == 1


async def test_play_video_propagates_not_found(db_session: AsyncSession) -> None:
    user_repo = UserRepository(db_session)
    video_repo = VideoRepository(db_session)
    series_repo = SeriesRepository(db_session)
    history_repo = HistoryRepository(db_session)
    progress_repo = WatchProgressRepository(db_session)

    video_service = VideoService(video_repo, series_repo)
    history_service = HistoryService(history_repo, progress_repo)
    playback_service = PlaybackService(video_service, history_service)

    user, _ = await user_repo.get_or_create(telegram_id=1)
    bot = AsyncMock()

    with pytest.raises(VideoNotFoundError):
        await playback_service.play_video(
            bot=bot, chat_id=user.telegram_id, user_id=user.id, video_id=99999
        )

    # No history should have been recorded since delivery failed.
    history = await history_service.get_history(user.id)
    assert history == []
