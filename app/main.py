"""
Application entrypoint.

Runs a FastAPI server (uvicorn/ASGI) that:
  - Exposes GET /health for platform healthchecks (Render, Koyeb, etc.).
  - Exposes POST {webhook_path} to receive Telegram Update objects.
  - Sets the Telegram webhook on startup, deletes it on shutdown.

We deliberately use FastAPI as the ASGI host instead of aiohttp
(aiogram's built-in webserver) so that non-Telegram concerns — health
checks, future REST endpoints for an eventual web frontend, metrics —
live naturally alongside the bot without extra wiring.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from aiogram.types import Update
from fastapi import FastAPI, Header, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.config.settings import get_settings
from app.core.bot import create_bot, create_dispatcher
from app.core.logging import setup_logging
from app.database.engine import create_engine, create_session_factory

settings = get_settings()
setup_logging(settings)
logger = logging.getLogger(__name__)

engine = create_engine(settings)
session_factory = create_session_factory(engine)

bot = create_bot(settings)
dispatcher = create_dispatcher(settings, session_factory)

# Register routers (imported here to avoid circular imports at module load)
from app.routers import main_router  # noqa: E402

dispatcher.include_router(main_router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Expose session_factory for REST API endpoints
    app.state.session_factory = session_factory
    logger.info("Starting up: setting Telegram webhook -> %s", settings.telegram.webhook_url)
    await bot.set_webhook(
        url=settings.telegram.webhook_url,
        secret_token=settings.telegram.webhook_secret_token.get_secret_value(),
        drop_pending_updates=True,
        allowed_updates=dispatcher.resolve_used_update_types(),
    )
    yield
    logger.info("Shutting down: deleting Telegram webhook")
    await bot.delete_webhook()
    await bot.session.close()
    await engine.dispose()


app = FastAPI(
    title="Telegram Video Platform",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS cho Mini App frontend (GitHub Pages hoặc bất kỳ domain nào)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# REST API cho Mini App
app.include_router(api_router)


@app.get("/health", status_code=status.HTTP_200_OK)
async def health() -> dict[str, Any]:
    """Platform healthcheck endpoint (Render, Koyeb, etc.)."""
    return {"status": "ok", "environment": settings.environment.value}


@app.post(settings.telegram.webhook_path)
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> Response:
    """Receive Telegram updates via webhook.

    Validates the secret token header on every request — this is the
    primary defense against spoofed requests hitting the endpoint,
    since the path itself is public.
    """
    expected = settings.telegram.webhook_secret_token.get_secret_value()
    if x_telegram_bot_api_secret_token != expected:
        logger.warning("Rejected webhook request with invalid secret token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid secret token")

    data = await request.json()
    update = Update.model_validate(data, context={"bot": bot})
    await dispatcher.feed_update(bot=bot, update=update)
    return Response(status_code=status.HTTP_200_OK)
