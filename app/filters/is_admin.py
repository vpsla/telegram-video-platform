"""
Admin permission filter.

Relies on data["user"] already being populated by UserMiddleware
(which sets is_admin based on AppSettings.admin_ids). Kept as a
standalone Filter — rather than checked inline in every handler — so
the entire admin router can be gated in one place:

    admin_router.message.filter(IsAdminFilter())
"""

from __future__ import annotations

from typing import Any

from aiogram.filters import Filter
from aiogram.types import TelegramObject

from app.database.models.user import User


class IsAdminFilter(Filter):
    async def __call__(self, event: TelegramObject, **data: Any) -> bool:
        user: User | None = data.get("user")
        return bool(user and user.is_admin)
