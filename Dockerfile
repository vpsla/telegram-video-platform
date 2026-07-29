# syntax=docker/dockerfile:1.7

# =============================================================================
# Stage 1: builder — resolve and install dependencies with uv into a venv
# =============================================================================
FROM python:3.12-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONDONTWRITEBYTECODE=1

COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/

WORKDIR /build

# Install deps first (better layer caching): only pyproject.toml + lock changes
# invalidate this layer, not application code changes.
# README.md must be copied alongside pyproject.toml because hatchling
# validates it exists (declared as readme = "README.md" in pyproject.toml).
COPY pyproject.toml README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv venv /opt/venv && \
    uv pip install --python /opt/venv/bin/python -e . --no-cache

COPY app ./app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --python /opt/venv/bin/python -e . --no-cache

# =============================================================================
# Stage 2: runtime — minimal image, no build tools, non-root user
# =============================================================================
FROM python:3.12-slim AS runtime

RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --chown=appuser:appuser app ./app
COPY --chown=appuser:appuser migrations ./migrations
COPY --chown=appuser:appuser alembic.ini ./alembic.ini

RUN mkdir -p /app/logs && chown appuser:appuser /app/logs

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx,os; httpx.get(f'http://127.0.0.1:{os.environ.get(\"PORT\",\"8000\")}/health').raise_for_status()" || exit 1

# Hosting platforms (Render, Koyeb, etc.) inject $PORT at runtime; default to 8000 for local docker-compose use.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
