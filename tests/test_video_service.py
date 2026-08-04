from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.category_repository import CategoryRepository
from app.database.repositories.series_repository import SeriesRepository
from app.database.repositories.video_repository import VideoRepository
from app.database.repositories.view_repository import ViewRepository
from app.services.video_service import VideoNotFoundError, VideoService


async def test_register_video_creates_new(db_session: AsyncSession) -> None:
    video_repo = VideoRepository(db_session)
    series_repo = SeriesRepository(db_session)
    service = VideoService(video_repo, series_repo)

    video = await service.register_video(channel_id=-1001111, message_id=1, title="Chương 1")
    assert video.id is not None
    assert video.title == "Chương 1"


async def test_register_video_is_idempotent(db_session: AsyncSession) -> None:
    video_repo = VideoRepository(db_session)
    series_repo = SeriesRepository(db_session)
    service = VideoService(video_repo, series_repo)

    first = await service.register_video(channel_id=-100, message_id=5, title="A")
    second = await service.register_video(channel_id=-100, message_id=5, title="A duplicate")

    assert first.id == second.id
    assert await video_repo.count_total() == 1


async def test_attach_to_series_increments_episode_count(db_session: AsyncSession) -> None:
    category_repo = CategoryRepository(db_session)
    series_repo = SeriesRepository(db_session)
    video_repo = VideoRepository(db_session)
    service = VideoService(video_repo, series_repo)

    category = await category_repo.create(name="Cat", slug="cat")
    series = await series_repo.create(category_id=category.id, title="S", slug="s")
    video = await service.register_video(channel_id=-100, message_id=1, title="Ep1")

    await service.attach_to_series(video_id=video.id, series_id=series.id, episode_number=1)

    reloaded_series = await series_repo.get_by_id(series.id)
    assert reloaded_series is not None
    assert reloaded_series.episode_count == 1


async def test_attach_to_series_twice_raises(db_session: AsyncSession) -> None:
    category_repo = CategoryRepository(db_session)
    series_repo = SeriesRepository(db_session)
    video_repo = VideoRepository(db_session)
    service = VideoService(video_repo, series_repo)

    category = await category_repo.create(name="Cat", slug="cat2")
    series = await series_repo.create(category_id=category.id, title="S", slug="s2")
    video = await service.register_video(channel_id=-100, message_id=2, title="Ep1")

    await service.attach_to_series(video_id=video.id, series_id=series.id, episode_number=1)
    with pytest.raises(ValueError):
        await service.attach_to_series(video_id=video.id, series_id=series.id, episode_number=2)


async def test_send_video_to_user_calls_copy_message_and_increments_view(
    db_session: AsyncSession,
) -> None:
    video_repo = VideoRepository(db_session)
    series_repo = SeriesRepository(db_session)
    service = VideoService(video_repo, series_repo)

    video = await service.register_video(channel_id=-1009999, message_id=77, title="Video")

    bot = AsyncMock()
    bot.copy_message = AsyncMock(return_value="sent_message_stub")

    result = await service.send_video_to_user(bot=bot, chat_id=12345, video_id=video.id)

    bot.copy_message.assert_awaited_once_with(chat_id=12345, from_chat_id=-1009999, message_id=77)
    assert result == "sent_message_stub"

    reloaded = await video_repo.get_by_id(video.id)
    assert reloaded is not None
    assert reloaded.view_count == 1


async def test_send_video_to_user_also_increments_series_views_when_episode(
    db_session: AsyncSession,
) -> None:
    category_repo = CategoryRepository(db_session)
    series_repo = SeriesRepository(db_session)
    video_repo = VideoRepository(db_session)
    service = VideoService(video_repo, series_repo)

    category = await category_repo.create(name="Cat", slug="cat3")
    series = await series_repo.create(category_id=category.id, title="S", slug="s3")
    video = await service.register_video(channel_id=-100, message_id=3, title="Ep1")
    await service.attach_to_series(video_id=video.id, series_id=series.id, episode_number=1)

    bot = AsyncMock()
    bot.copy_message = AsyncMock(return_value="ok")

    await service.send_video_to_user(bot=bot, chat_id=1, video_id=video.id)

    reloaded_series = await series_repo.get_by_id(series.id)
    assert reloaded_series is not None
    assert reloaded_series.total_views == 1


async def test_send_video_to_user_raises_for_missing_video(db_session: AsyncSession) -> None:
    video_repo = VideoRepository(db_session)
    series_repo = SeriesRepository(db_session)
    service = VideoService(video_repo, series_repo)

    bot = AsyncMock()
    with pytest.raises(VideoNotFoundError):
        await service.send_video_to_user(bot=bot, chat_id=1, video_id=99999)
    bot.copy_message.assert_not_awaited()


async def test_send_video_to_user_raises_for_hidden_video(db_session: AsyncSession) -> None:
    video_repo = VideoRepository(db_session)
    series_repo = SeriesRepository(db_session)
    service = VideoService(video_repo, series_repo)

    video = await service.register_video(channel_id=-100, message_id=99, title="Hidden")
    await video_repo.set_hidden(video.id, hidden=True)

    bot = AsyncMock()
    with pytest.raises(VideoNotFoundError):
        await service.send_video_to_user(bot=bot, chat_id=1, video_id=video.id)
    bot.copy_message.assert_not_awaited()


async def test_send_video_to_user_records_view_when_view_repo_provided(
    db_session: AsyncSession,
) -> None:
    video_repo = VideoRepository(db_session)
    series_repo = SeriesRepository(db_session)
    view_repo = ViewRepository(db_session)
    service = VideoService(video_repo, series_repo, view_repo)

    video = await service.register_video(channel_id=-100, message_id=1, title="V")

    bot = AsyncMock()
    bot.copy_message = AsyncMock(return_value="ok")

    await service.send_video_to_user(bot=bot, chat_id=1, video_id=video.id, viewer_user_id=42)

    assert await view_repo.count_total() == 1


async def test_send_video_to_user_without_view_repo_does_not_error(
    db_session: AsyncSession,
) -> None:
    """VideoService remains backward compatible: no view_repo passed
    means no View row is written, but the call still succeeds (Phase 3
    call sites that predate Phase 6 keep working unmodified)."""
    video_repo = VideoRepository(db_session)
    series_repo = SeriesRepository(db_session)
    service = VideoService(video_repo, series_repo)  # no view_repo

    video = await service.register_video(channel_id=-100, message_id=2, title="V2")

    bot = AsyncMock()
    bot.copy_message = AsyncMock(return_value="ok")

    result = await service.send_video_to_user(bot=bot, chat_id=1, video_id=video.id)
    assert result == "ok"
