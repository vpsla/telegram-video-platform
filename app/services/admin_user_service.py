"""Admin user-management service — thin wrapper adding admin-facing
validation/logging on top of UserRepository."""

from __future__ import annotations

import logging
from datetime import datetime

from app.database.models.user import User
from app.database.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class UserNotFoundError(Exception):
    pass


class AdminUserService:
    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    async def ban_user(self, user_id: int, *, reason: str) -> None:
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(f"User {user_id} not found")
        await self._user_repo.set_banned(user_id, banned=True, reason=reason)
        logger.info("Admin banned user_id=%s reason=%s", user_id, reason)

    async def unban_user(self, user_id: int) -> None:
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(f"User {user_id} not found")
        await self._user_repo.set_banned(user_id, banned=False)
        logger.info("Admin unbanned user_id=%s", user_id)

    async def grant_vip(self, user_id: int, *, expires_at: datetime | None = None) -> None:
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(f"User {user_id} not found")
        await self._user_repo.set_vip(user_id, vip=True, expires_at=expires_at)
        logger.info("Admin granted VIP to user_id=%s expires_at=%s", user_id, expires_at)

    async def revoke_vip(self, user_id: int) -> None:
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(f"User {user_id} not found")
        await self._user_repo.set_vip(user_id, vip=False)
        logger.info("Admin revoked VIP from user_id=%s", user_id)

    async def find_by_telegram_id(self, telegram_id: int) -> User | None:
        return await self._user_repo.get_by_telegram_id(telegram_id)

    async def list_users(self, *, offset: int = 0, limit: int = 20) -> list[User]:
        return await self._user_repo.list_paginated(offset=offset, limit=limit)
