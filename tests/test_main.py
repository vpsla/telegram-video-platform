from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def client():
    # Imported lazily so conftest env vars are set first.
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def test_health_endpoint(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"


async def test_webhook_rejects_missing_secret(client: AsyncClient) -> None:
    response = await client.post("/webhook/telegram", json={"update_id": 1})
    assert response.status_code == 401


async def test_webhook_rejects_wrong_secret(client: AsyncClient) -> None:
    response = await client.post(
        "/webhook/telegram",
        json={"update_id": 1},
        headers={"X-Telegram-Bot-Api-Secret-Token": "wrong"},
    )
    assert response.status_code == 401
