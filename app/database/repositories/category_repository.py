"""Category repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.category import Category


class CategoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, category_id: int) -> Category | None:
        return await self._session.get(Category, category_id)

    async def get_by_slug(self, slug: str) -> Category | None:
        stmt = select(Category).where(Category.slug == slug)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        name: str,
        slug: str,
        description: str | None = None,
        icon_emoji: str | None = None,
        display_order: int = 0,
    ) -> Category:
        category = Category(
            name=name,
            slug=slug,
            description=description,
            icon_emoji=icon_emoji,
            display_order=display_order,
        )
        self._session.add(category)
        await self._session.flush()
        return category

    async def update(
        self,
        category_id: int,
        *,
        name: str | None = None,
        description: str | None = None,
        icon_emoji: str | None = None,
        display_order: int | None = None,
    ) -> Category:
        category = await self.get_by_id(category_id)
        if category is None:
            raise ValueError(f"Category {category_id} not found")
        if name is not None:
            category.name = name
        if description is not None:
            category.description = description
        if icon_emoji is not None:
            category.icon_emoji = icon_emoji
        if display_order is not None:
            category.display_order = display_order
        await self._session.flush()
        return category

    async def set_active(self, category_id: int, *, active: bool) -> None:
        category = await self.get_by_id(category_id)
        if category is None:
            raise ValueError(f"Category {category_id} not found")
        category.is_active = active
        await self._session.flush()

    async def delete(self, category_id: int) -> None:
        category = await self.get_by_id(category_id)
        if category is None:
            raise ValueError(f"Category {category_id} not found")
        await self._session.delete(category)
        await self._session.flush()

    async def list_active(self) -> list[Category]:
        stmt = (
            select(Category)
            .where(Category.is_active.is_(True))
            .order_by(Category.display_order, Category.name)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_all(self) -> list[Category]:
        stmt = select(Category).order_by(Category.display_order, Category.name)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
