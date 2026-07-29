"""
Structured logging setup.

- Console handler: human-readable, for local dev and platform log streams (Render, Koyeb, etc.).
- Rotating file handler: JSON lines, for persistent/parsable logs.
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from pythonjsonlogger.json import JsonFormatter

from app.config.settings import AppSettings

CONSOLE_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
JSON_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s %(module)s %(funcName)s %(lineno)d"


def setup_logging(settings: AppSettings) -> None:
    """Configure root logger with console + rotating file handlers.

    Idempotent: safe to call multiple times (e.g. in tests) without
    duplicating handlers.
    """
    root = logging.getLogger()
    root.setLevel(settings.log_level.upper())

    # Avoid duplicate handlers on reload/hot-restart
    if root.handlers:
        root.handlers.clear()

    # --- Console handler ---------------------------------------------------
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(CONSOLE_FORMAT))
    console_handler.setLevel(settings.log_level.upper())
    root.addHandler(console_handler)

    # --- Rotating file handler ----------------------------------------------
    log_dir = Path(settings.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        filename=log_dir / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(JsonFormatter(JSON_FORMAT))
    file_handler.setLevel(logging.INFO)
    root.addHandler(file_handler)

    # Quiet down noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("aiogram.event").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.database.echo else logging.WARNING
    )

    root.info(
        "Logging initialized (level=%s, env=%s)",
        settings.log_level,
        settings.environment.value,
    )
