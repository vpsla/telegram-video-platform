from __future__ import annotations

from unittest.mock import MagicMock

from app.database.models.user import User
from app.filters.is_admin import IsAdminFilter


async def test_is_admin_filter_true_for_admin_user() -> None:
    filt = IsAdminFilter()
    admin_user = User(telegram_id=1, is_admin=True)
    result = await filt(MagicMock(), user=admin_user)
    assert result is True


async def test_is_admin_filter_false_for_regular_user() -> None:
    filt = IsAdminFilter()
    regular_user = User(telegram_id=2, is_admin=False)
    result = await filt(MagicMock(), user=regular_user)
    assert result is False


async def test_is_admin_filter_false_when_no_user_in_data() -> None:
    filt = IsAdminFilter()
    result = await filt(MagicMock())
    assert result is False
