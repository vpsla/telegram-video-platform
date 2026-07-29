from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.config.settings import AppSettings, TelegramSettings


def test_settings_load(settings: AppSettings) -> None:
    assert settings.telegram.bot_token.get_secret_value() == "000000:TEST-TOKEN-NOT-REAL"
    assert settings.telegram.storage_channel_id == -1001111111111
    assert settings.telegram.webhook_url == "https://example.com/webhook/telegram"


def test_admin_ids_parsed_from_csv(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ADMIN_IDS", "111,222, 333")
    from app.config.settings import get_settings

    get_settings.cache_clear()
    s = get_settings()
    assert s.admin_ids == [111, 222, 333]


def test_positive_channel_id_rejected() -> None:
    with pytest.raises(ValidationError):
        TelegramSettings(
            bot_token="x",
            storage_channel_id=12345,  # must be negative
            webhook_base_url="https://example.com",
            webhook_secret_token="secret",
        )
