from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.user_repository import UserRepository
from app.database.repositories.video_repository import VideoRepository
from app.database.repositories.view_repository import ViewRepository


async def _setup(db_session: AsyncSession, n_videos: int = 2, n_users: int = 2):
    video_repo = VideoRepository(db_session)
    user_repo = UserRepository(db_session)
    videos = [
        await video_repo.create(channel_id=-100, message_id=i, title=f"V{i}")
        for i in range(1, n_videos + 1)
    ]
    users = []
    for i in range(1, n_users + 1):
        user, _ = await user_repo.get_or_create(telegram_id=i)
        users.append(user)
    return videos, users


async def test_record_and_count_total(db_session: AsyncSession) -> None:
    videos, users = await _setup(db_session, n_videos=1, n_users=1)
    repo = ViewRepository(db_session)

    await repo.record(video_id=videos[0].id, user_id=users[0].id)
    await repo.record(video_id=videos[0].id, user_id=None)  # anonymous view allowed

    assert await repo.count_total() == 2


async def test_count_since(db_session: AsyncSession) -> None:
    videos, users = await _setup(db_session, n_videos=1, n_users=1)
    repo = ViewRepository(db_session)
    await repo.record(video_id=videos[0].id, user_id=users[0].id)

    future_cutoff = datetime.now(UTC) + timedelta(days=1)
    assert await repo.count_since(future_cutoff) == 0

    past_cutoff = datetime.now(UTC) - timedelta(days=1)
    assert await repo.count_since(past_cutoff) == 1


async def test_top_video_ids_orders_by_count_desc(db_session: AsyncSession) -> None:
    videos, users = await _setup(db_session, n_videos=2, n_users=1)
    repo = ViewRepository(db_session)

    # video[0] gets 3 views, video[1] gets 1 view
    for _ in range(3):
        await repo.record(video_id=videos[0].id, user_id=users[0].id)
    await repo.record(video_id=videos[1].id, user_id=users[0].id)

    since = datetime.now(UTC) - timedelta(days=1)
    top = await repo.top_video_ids(since=since, limit=10)

    assert top[0] == (videos[0].id, 3)
    assert top[1] == (videos[1].id, 1)


async def test_top_viewer_user_ids_excludes_anonymous(db_session: AsyncSession) -> None:
    videos, users = await _setup(db_session, n_videos=1, n_users=2)
    repo = ViewRepository(db_session)

    await repo.record(video_id=videos[0].id, user_id=users[0].id)
    await repo.record(video_id=videos[0].id, user_id=users[0].id)
    await repo.record(video_id=videos[0].id, user_id=users[1].id)
    await repo.record(video_id=videos[0].id, user_id=None)  # should be excluded

    since = datetime.now(UTC) - timedelta(days=1)
    top = await repo.top_viewer_user_ids(since=since, limit=10)

    assert top[0] == (users[0].id, 2)
    assert len(top) == 2  # anonymous view not counted as a viewer


async def test_views_per_day_groups_correctly(db_session: AsyncSession) -> None:
    videos, users = await _setup(db_session, n_videos=1, n_users=1)
    repo = ViewRepository(db_session)

    await repo.record(video_id=videos[0].id, user_id=users[0].id)
    await repo.record(video_id=videos[0].id, user_id=users[0].id)

    since = datetime.now(UTC) - timedelta(days=1)
    daily = await repo.views_per_day(since)

    assert len(daily) == 1  # both views recorded today, same bucket
    assert daily[0][1] == 2
