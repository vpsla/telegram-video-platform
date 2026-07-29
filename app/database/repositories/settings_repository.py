"""Settings (key-value config) repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.settings import Settings


class SettingsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, key: str) -> Settings | None:
        return await self._session.get(Settings, key)

    async def get_value(self, key: str, default: str | None = None) -> str | None:
        setting = await self.get(key)
        return setting.value if setting is not None else default

    async def set(self, key: str, value: str, *, description: str | None = None) -> Settings:
        setting = await self.get(key)
        if setting is None:
            setting = Settings(key=key, value=value, description=description)
            self._session.add(setting)
        else:
            setting.value = value
            if description is not None:
                setting.description = description
        await self._session.flush()
        return setting

    async def delete(self, key: str) -> bool:
        setting = await self.get(key)
        if setting is None:
            return False
        await self._session.delete(setting)
        await self._session.flush()
        return True

    async def list_all(self) -> list[Settings]:
        stmt = select(Settings).order_by(Settings.key)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
