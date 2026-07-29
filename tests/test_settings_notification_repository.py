from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.notification import NotificationType
from app.database.repositories.notification_repository import NotificationRepository
from app.database.repositories.settings_repository import SettingsRepository
from app.database.repositories.user_repository import UserRepository


async def test_settings_set_and_get(db_session: AsyncSession) -> None:
    repo = SettingsRepository(db_session)
    await repo.set("maintenance_mode", "false", description="Toggle maintenance banner")

    value = await repo.get_value("maintenance_mode")
    assert value == "false"


async def test_settings_set_updates_existing(db_session: AsyncSession) -> None:
    repo = SettingsRepository(db_session)
    await repo.set("key1", "value1")
    await repo.set("key1", "value2")

    assert await repo.get_value("key1") == "value2"
    all_settings = await repo.list_all()
    assert len(all_settings) == 1


async def test_settings_get_value_default(db_session: AsyncSession) -> None:
    repo = SettingsRepository(db_session)
    assert await repo.get_value("missing_key", default="fallback") == "fallback"


async def test_settings_delete(db_session: AsyncSession) -> None:
    repo = SettingsRepository(db_session)
    await repo.set("temp", "x")
    assert await repo.delete("temp") is True
    assert await repo.get("temp") is None
    assert await repo.delete("temp") is False


async def test_notification_create_and_mark_sent(db_session: AsyncSession) -> None:
    user_repo = UserRepository(db_session)
    user, _ = await user_repo.get_or_create(telegram_id=1)
    repo = NotificationRepository(db_session)

    notification = await repo.create(
        user_id=user.id,
        notification_type=NotificationType.NEW_EPISODE,
        title="Tập mới!",
        body="Series X vừa có tập mới.",
    )
    assert notification.is_sent is False

    await repo.mark_sent(notification.id)
    notifications = await repo.list_for_user(user.id)
    assert notifications[0].is_sent is True


async def test_notification_mark_failed(db_session: AsyncSession) -> None:
    user_repo = UserRepository(db_session)
    user, _ = await user_repo.get_or_create(telegram_id=2)
    repo = NotificationRepository(db_session)

    notification = await repo.create(
        user_id=user.id, notification_type=NotificationType.BROADCAST, title="Test"
    )
    await repo.mark_failed(notification.id, "User blocked bot")

    notifications = await repo.list_for_user(user.id)
    assert notifications[0].is_sent is False
    assert notifications[0].error_message == "User blocked bot"
