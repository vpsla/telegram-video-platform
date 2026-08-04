from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.category_repository import CategoryRepository
from app.database.repositories.favorite_repository import FavoriteRepository
from app.database.repositories.series_repository import SeriesRepository
from app.database.repositories.user_repository import UserRepository


async def _setup(db_session: AsyncSession):
    user_repo = UserRepository(db_session)
    category_repo = CategoryRepository(db_session)
    series_repo = SeriesRepository(db_session)

    user, _ = await user_repo.get_or_create(telegram_id=1)
    category = await category_repo.create(name="Cat", slug="cat")
    series = await series_repo.create(category_id=category.id, title="S", slug="s")
    return user, series


async def test_add_and_is_following(db_session: AsyncSession) -> None:
    user, series = await _setup(db_session)
    repo = FavoriteRepository(db_session)

    assert await repo.is_following(user.id, series.id) is False
    await repo.add(user.id, series.id)
    assert await repo.is_following(user.id, series.id) is True


async def test_add_is_idempotent(db_session: AsyncSession) -> None:
    user, series = await _setup(db_session)
    repo = FavoriteRepository(db_session)

    f1 = await repo.add(user.id, series.id)
    f2 = await repo.add(user.id, series.id)
    assert f1.id == f2.id
    assert await repo.count_for_user(user.id) == 1


async def test_remove(db_session: AsyncSession) -> None:
    user, series = await _setup(db_session)
    repo = FavoriteRepository(db_session)
    await repo.add(user.id, series.id)

    removed = await repo.remove(user.id, series.id)
    assert removed is True
    assert await repo.is_following(user.id, series.id) is False

    removed_again = await repo.remove(user.id, series.id)
    assert removed_again is False


async def test_list_for_user_eager_loads_series_and_category(db_session: AsyncSession) -> None:
    user, series = await _setup(db_session)
    repo = FavoriteRepository(db_session)
    await repo.add(user.id, series.id)

    favorites = await repo.list_for_user(user.id)
    assert len(favorites) == 1
    assert favorites[0].series.category.slug == "cat"  # no lazy-load error


async def test_list_follower_user_ids(db_session: AsyncSession) -> None:
    user_repo = UserRepository(db_session)
    _, series = await _setup(db_session)
    repo = FavoriteRepository(db_session)

    user1, _ = await user_repo.get_or_create(telegram_id=100)
    user2, _ = await user_repo.get_or_create(telegram_id=200)
    await repo.add(user1.id, series.id)
    await repo.add(user2.id, series.id)

    follower_ids = await repo.list_follower_user_ids(series.id)
    assert set(follower_ids) == {user1.id, user2.id}
