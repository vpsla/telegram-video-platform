#!/usr/bin/env bash
# =============================================================================
# One-command local setup for Telegram Video Platform.
#
# Usage:
#   chmod +x scripts/setup.sh
#   ./scripts/setup.sh
#
# What it does:
#   1. Checks for required tools (python3, uv, docker).
#   2. Creates .env from .env.example if missing, prompting for the
#      values that MUST be filled in manually (secrets are never
#      auto-generated blindly — token/channel ID must come from you).
#   3. Installs Python dependencies with uv.
#   4. Optionally starts docker compose (local Postgres) and runs
#      Alembic migrations.
#
# This script is idempotent: safe to re-run. It never overwrites an
# existing .env — if one is present, it's left untouched and you'll be
# told to edit it manually instead.
# =============================================================================
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${GREEN}==>${NC} $1"; }
warn()  { echo -e "${YELLOW}==>${NC} $1"; }
error() { echo -e "${RED}==>${NC} $1"; }

# --- 1. Check prerequisites --------------------------------------------------
info "Kiểm tra công cụ cần thiết..."

if ! command -v python3 &>/dev/null; then
    error "Không tìm thấy python3. Cài Python 3.12+ trước: https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
info "Python: $PYTHON_VERSION"

if ! command -v uv &>/dev/null; then
    warn "Không tìm thấy 'uv'. Đang cài đặt..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi
info "uv: $(uv --version)"

HAS_DOCKER=false
if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
    HAS_DOCKER=true
    info "Docker: có sẵn"
else
    warn "Không có Docker (hoặc Docker daemon chưa chạy). Sẽ bỏ qua bước docker compose."
fi

# --- 2. Set up .env -----------------------------------------------------------
if [ -f .env ]; then
    warn ".env đã tồn tại — giữ nguyên, không ghi đè. Sửa tay nếu cần thay đổi giá trị."
else
    info "Tạo .env từ .env.example..."
    cp .env.example .env

    echo ""
    echo -e "${BOLD}Cần điền các giá trị bắt buộc sau (Enter để bỏ qua và tự điền sau trong .env):${NC}"

    read -rp "  TELEGRAM_BOT_TOKEN (từ @BotFather): " BOT_TOKEN
    read -rp "  TELEGRAM_STORAGE_CHANNEL_ID (dạng -100xxxxxxxxxx): " CHANNEL_ID
    read -rp "  DATABASE_URL (Supabase Connection Pooling URI, để trống dùng Postgres local): " DB_URL
    read -rp "  ADMIN_IDS (telegram_id của bạn, phân cách dấu phẩy nếu nhiều): " ADMIN_IDS

    GENERATED_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")

    # Portable in-place sed (works on both GNU sed and BSD/macOS sed)
    sed_inplace() {
        if sed --version >/dev/null 2>&1; then
            sed -i "$1" .env
        else
            sed -i '' "$1" .env
        fi
    }

    [ -n "$BOT_TOKEN" ] && sed_inplace "s#^TELEGRAM_BOT_TOKEN=.*#TELEGRAM_BOT_TOKEN=${BOT_TOKEN}#"
    [ -n "$CHANNEL_ID" ] && sed_inplace "s#^TELEGRAM_STORAGE_CHANNEL_ID=.*#TELEGRAM_STORAGE_CHANNEL_ID=${CHANNEL_ID}#"
    [ -n "$DB_URL" ] && sed_inplace "s#^DATABASE_URL=.*#DATABASE_URL=${DB_URL}#"
    [ -n "$ADMIN_IDS" ] && sed_inplace "s#^ADMIN_IDS=.*#ADMIN_IDS=${ADMIN_IDS}#"
    sed_inplace "s#^TELEGRAM_WEBHOOK_SECRET_TOKEN=.*#TELEGRAM_WEBHOOK_SECRET_TOKEN=${GENERATED_SECRET}#"

    info "Đã tự sinh TELEGRAM_WEBHOOK_SECRET_TOKEN ngẫu nhiên."
    warn "Nhớ điền TELEGRAM_WEBHOOK_BASE_URL sau khi deploy (Render hoặc ngrok)."
fi

# --- 3. Install dependencies ---------------------------------------------------
info "Cài đặt Python dependencies..."
uv venv --allow-existing
# shellcheck disable=SC1091
source .venv/bin/activate
uv pip install -e ".[dev]"

# --- 4. Optional: start local Postgres + run migrations ------------------------
if [ "$HAS_DOCKER" = true ]; then
    read -rp "Khởi động Postgres local qua docker compose và chạy migration? (y/N): " START_DB
    if [[ "$START_DB" =~ ^[Yy]$ ]]; then
        info "Khởi động Postgres local..."
        docker compose up -d db

        info "Chờ Postgres sẵn sàng..."
        until docker compose exec -T db pg_isready -U postgres &>/dev/null; do
            sleep 1
        done

        info "Chạy Alembic migration..."
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/postgres" \
            alembic upgrade head || warn "Migration thất bại — có thể .env dùng DATABASE_URL khác (Supabase) thay vì Postgres local."
    fi
fi

echo ""
info "Cài đặt hoàn tất!"
echo ""
echo "Bước tiếp theo:"
echo "  1. Kiểm tra lại .env — đặc biệt TELEGRAM_WEBHOOK_BASE_URL"
echo "  2. Chạy thử:      docker compose up --build"
echo "     hoặc:          uvicorn app.main:app --reload --port 8000"
echo "  3. Kiểm tra:       curl http://localhost:8000/health"
echo "  4. Chạy test:      pytest"
