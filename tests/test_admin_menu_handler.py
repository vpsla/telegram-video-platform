"""
Smoke test for the admin menu handler.

Rather than wiring a full Dispatcher (which requires juggling
module-level Router singletons across tests), this calls the handler
function directly with a mocked Message -- this is the standard
aiogram testing pattern and is sufficient since IsAdminFilter itself
is already covered by tests/test_is_admin_filter.py and the
end-to-end middleware chain is covered by tests/test_user_middleware.py.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

from app.handlers.admin.menu import handle_admin_menu


async def test_admin_menu_sends_keyboard() -> None:
    message = AsyncMock()
    message.answer = AsyncMock()

    await handle_admin_menu(message)

    message.answer.assert_awaited_once()
    args, kwargs = message.answer.await_args
    text = args[0] if args else kwargs.get("text", "")
    assert "Bảng điều khiển Admin" in text
    assert kwargs.get("reply_markup") is not None
