from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.category_repository import CategoryRepository


async def test_create_and_get_category(db_session: AsyncSession) -> None:
    repo = CategoryRepository(db_session)
    category = await repo.create(name="Tiên Hiệp", slug="tien-hiep", icon_emoji="⚔️")

    fetched = await repo.get_by_id(category.id)
    assert fetched is not None
    assert fetched.slug == "tien-hiep"
    assert fetched.is_active is True


async def test_get_by_slug(db_session: AsyncSession) -> None:
    repo = CategoryRepository(db_session)
    await repo.create(name="Đô Thị", slug="do-thi")

    fetched = await repo.get_by_slug("do-thi")
    assert fetched is not None
    assert fetched.name == "Đô Thị"

    assert await repo.get_by_slug("khong-ton-tai") is None


async def test_update_category(db_session: AsyncSession) -> None:
    repo = CategoryRepository(db_session)
    category = await repo.create(name="Huyền Huyễn", slug="huyen-huyen")

    updated = await repo.update(category.id, name="Huyền Huyễn (updated)", display_order=5)
    assert updated.name == "Huyền Huyễn (updated)"
    assert updated.display_order == 5


async def test_set_active_and_list_active(db_session: AsyncSession) -> None:
    repo = CategoryRepository(db_session)
    c1 = await repo.create(name="A", slug="a", display_order=1)
    c2 = await repo.create(name="B", slug="b", display_order=2)

    await repo.set_active(c2.id, active=False)

    active = await repo.list_active()
    assert [c.slug for c in active] == ["a"]

    all_categories = await repo.list_all()
    assert len(all_categories) == 2
    assert c1.slug == "a"


async def test_delete_category(db_session: AsyncSession) -> None:
    repo = CategoryRepository(db_session)
    category = await repo.create(name="Temp", slug="temp")
    await repo.delete(category.id)

    assert await repo.get_by_id(category.id) is None


async def test_update_unknown_category_raises(db_session: AsyncSession) -> None:
    repo = CategoryRepository(db_session)
    with pytest.raises(ValueError):
        await repo.update(99999, name="x")
