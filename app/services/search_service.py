"""
Search service.

Coordinates SeriesRepository/CategoryRepository to satisfy the search
requirements from the spec: by name, by category, by series, by tag,
by author, and approximate keyword search. All of these ultimately
reduce to SeriesRepository.search() (ILIKE across title/author/tags)
or SeriesRepository.list_by_category() — this service exists so
handlers have one entry point regardless of which filter the user picked,
instead of branching directly on repository methods.
"""

from __future__ import annotations

from app.database.models.series import Series
from app.database.repositories.category_repository import CategoryRepository
from app.database.repositories.series_repository import SeriesRepository


class CategoryNotFoundError(Exception):
    pass


class SearchService:
    def __init__(self, series_repo: SeriesRepository, category_repo: CategoryRepository) -> None:
        self._series_repo = series_repo
        self._category_repo = category_repo

    async def search_by_keyword(
        self, keyword: str, *, offset: int = 0, limit: int = 20
    ) -> list[Series]:
        """Approximate search across title, author, and tags."""
        keyword = keyword.strip()
        if not keyword:
            return []
        return await self._series_repo.search(keyword, offset=offset, limit=limit)

    async def search_by_category_slug(
        self, category_slug: str, *, offset: int = 0, limit: int = 20
    ) -> list[Series]:
        category = await self._category_repo.get_by_slug(category_slug)
        if category is None:
            raise CategoryNotFoundError(f"Category slug {category_slug!r} not found")
        return await self._series_repo.list_by_category(category.id, offset=offset, limit=limit)

    async def get_series_by_slug(self, series_slug: str) -> Series | None:
        return await self._series_repo.get_by_slug(series_slug)
