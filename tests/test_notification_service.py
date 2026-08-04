from __future__ import annotations

from unittest.mock import AsyncMock

from aiogram.exceptions import TelegramForbiddenError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.category_repository import CategoryRepository
from app.database.repositories.favorite_repository import FavoriteRepository
from app.database.repositories.notification_repository import NotificationRepository
from app.database.repositories.series_repository import SeriesRepository
from app.database.repositories.user_repository import UserRepository
from app.services.notification_service import NotificationService


def _make_forbidden_error() -> TelegramForbiddenError:
    request = AsyncMock()
    request.method = "sendMessage"
    return TelegramForbiddenError(method=request, message="Forbidden: bot was blocked")


async def _setup_series_with_followers(db_session: AsyncSession, n_followers: int = 2):
    category_repo = CategoryRepository(db_session)
    series_repo = SeriesRepository(db_session)
    user_repo = UserRepository(db_session)
    favorite_repo = FavoriteRepository(db_session)

    category = await category_repo.create(name="Cat", slug="cat")
    series = await series_repo.create(category_id=category.id, title="Series X", slug="series-x")

    followers = []
    for i in range(n_followers):
        user, _ = await user_repo.get_or_create(telegram_id=i + 1)
        await favorite_repo.add(user.id, series.id)
        followers.append(user)

    return series, followers


async def test_notify_new_episode_sends_to_all_followers(db_session: AsyncSession) -> None:
    series, _followers = await _setup_series_with_followers(db_session, n_followers=3)

    service = NotificationService(
        NotificationRepository(db_session),
        FavoriteRepository(db_session),
        UserRepository(db_session),
    )
    bot = AsyncMock()
    bot.send_message = AsyncMock(return_value=None)

    sent_count = await service.notify_new_episode(
        bot=bot, series_id=series.id, series_title=series.title, episode_number=5
    )

    assert sent_count == 3
    assert bot.send_message.await_count == 3


async def test_notify_new_episode_no_followers(db_session: AsyncSession) -> None:
    category_repo = CategoryRepository(db_session)
    series_repo = SeriesRepository(db_session)
    category = await category_repo.create(name="Cat", slug="cat2")
    series = await series_repo.create(category_id=category.id, title="Lonely Series", slug="l")

    service = NotificationService(
        NotificationRepository(db_session),
        FavoriteRepository(db_session),
        UserRepository(db_session),
    )
    bot = AsyncMock()

    sent_count = await service.notify_new_episode(
        bot=bot, series_id=series.id, series_title=series.title, episode_number=1
    )

    assert sent_count == 0
    bot.send_message.assert_not_awaited()


async def test_notify_new_episode_isolates_forbidden_error(db_session: AsyncSession) -> None:
    series, followers = await _setup_series_with_followers(db_session, n_followers=2)

    notification_repo = NotificationRepository(db_session)
    service = NotificationService(
        notification_repo,
        FavoriteRepository(db_session),
        UserRepository(db_session),
    )
    bot = AsyncMock()
    bot.send_message = AsyncMock(side_effect=[_make_forbidden_error(), None])

    sent_count = await service.notify_new_episode(
        bot=bot, series_id=series.id, series_title=series.title, episode_number=2
    )

    assert sent_count == 1  # one blocked, one succeeded

    all_notifications = []
    for follower in followers:
        all_notifications.extend(await notification_repo.list_for_user(follower.id))
    failed = [n for n in all_notifications if n.error_message]
    assert len(failed) == 1
    assert failed[0].error_message == "User blocked bot"


async def test_notify_new_episode_skips_banned_users(db_session: AsyncSession) -> None:
    series, followers = await _setup_series_with_followers(db_session, n_followers=2)

    user_repo = UserRepository(db_session)
    await user_repo.set_banned(followers[0].id, banned=True, reason="spam")

    service = NotificationService(
        NotificationRepository(db_session),
        FavoriteRepository(db_session),
        user_repo,
    )
    bot = AsyncMock()
    bot.send_message = AsyncMock(return_value=None)

    sent_count = await service.notify_new_episode(
        bot=bot, series_id=series.id, series_title=series.title, episode_number=1
    )

    assert sent_count == 1
    assert bot.send_message.await_count == 1
