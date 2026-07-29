# Telegram Video Platform

Nền tảng xem video truyện/audio dạng YouTube, sử dụng **Telegram Channel** làm nơi lưu trữ video và **Telegram Bot** làm giao diện quản lý/phát lại.

> 📌 Dự án đã hoàn thành đầy đủ **7 Phase** phát triển (xem mục "Lộ trình phát triển" cuối trang).

## 🚀 Cài đặt nhanh

### Deploy online (gần 1-click, dùng Render)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/YOUR-USERNAME/YOUR-REPO)

**Trước khi bấm nút:**
1. Push code này lên GitHub repo của riêng bạn (Render build trực tiếp từ GitHub, không build được từ file zip).
2. Sửa `YOUR-USERNAME/YOUR-REPO` trong link trên thành đường dẫn repo thật của bạn.
3. Chạy migration lên Supabase trước (xem mục "Deploy lên Render" bên dưới, Bước 1) — Render không tự chạy Alembic.

**Cách hoạt động:** repo này đã có sẵn file [`render.yaml`](./render.yaml) (Render Blueprint) — Render tự đọc file này khi bấm nút, tự điền sẵn builder (Dockerfile), health check (`/health`), và tự sinh `TELEGRAM_WEBHOOK_SECRET_TOKEN` ngẫu nhiên. Bạn chỉ cần điền 4 giá trị được Render **hỏi trực tiếp trên Dashboard lúc tạo Blueprint** (không phải trong URL, nên không lộ secret): `TELEGRAM_BOT_TOKEN`, `TELEGRAM_STORAGE_CHANNEL_ID`, `DATABASE_URL`, `ADMIN_IDS`. Sau khi có domain `*.onrender.com`, quay lại điền `TELEGRAM_WEBHOOK_BASE_URL` (xem chi tiết ở Bước 5 mục Deploy).

> ⚠️ **Lưu ý về free tier của Render:** service Free tự "ngủ" sau 15 phút không có traffic, và mất khoảng 30-60 giây để "thức dậy" khi có request mới. Vì bot dùng **webhook** (không phải polling), nếu service đang ngủ thì update từ Telegram có thể bị trễ hoặc timeout. Xem mục "Free tier & cold start" ở phần Deploy bên dưới để biết cách khắc phục miễn phí (ping định kỳ).

### Cài đặt local tự động

```bash
git clone <your-repo-url>
cd telegram-video-platform
chmod +x scripts/setup.sh
./scripts/setup.sh
```

Script sẽ tự kiểm tra Python/uv/Docker, tạo `.env` và hỏi các giá trị cần thiết (bot token, channel ID, DB URL...), tự sinh `TELEGRAM_WEBHOOK_SECRET_TOKEN` ngẫu nhiên, cài dependencies, và tùy chọn khởi động Postgres local + chạy migration. Chạy lại an toàn — không ghi đè `.env` đã có.

## Kiến trúc

Clean Architecture, chia layer rõ ràng:

```
app/
├── config/          # Pydantic Settings (env vars)
├── core/            # Bot/Dispatcher factory, logging
├── database/
│   ├── models/       # SQLAlchemy ORM models (Phase 2+)
│   └── repositories/ # Data access layer (Phase 2+)
├── services/         # Business logic (Phase 2+)
├── handlers/          # Aiogram message/callback handlers
│   ├── admin/
│   └── user/
├── middlewares/       # Rate limit, auth, DB session injection
├── filters/            # Custom aiogram filters
├── keyboards/           # InlineKeyboard builders
├── states/               # FSM states
├── routers/                # Router composition (admin/user)
├── utils/
├── scheduler/               # Background jobs (notifications, stats)
└── main.py                   # FastAPI app: webhook + health endpoints
```

## Công nghệ

- Python 3.12+, Aiogram 3.x, SQLAlchemy 2.x (async) + Alembic
- Supabase PostgreSQL (không dùng SQLite)
- FastAPI + Uvicorn làm ASGI host cho webhook (không dùng polling)
- Redis (tùy chọn, tắt mặc định — dùng cho FSM storage/rate-limit khi bật)
- Docker multi-stage build, deploy trên Render
- `uv` package manager, Ruff + Black, Pytest

## Cài đặt (local)

### 1. Yêu cầu

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (`pip install uv` hoặc xem hướng dẫn cài đặt chính thức)
- Docker + Docker Compose (khuyến nghị để chạy kèm Postgres local)

### 2. Cài dependencies

```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

### 3. Cấu hình môi trường

```bash
cp .env.example .env
```

Điền các giá trị:

| Biến | Mô tả |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Token bot lấy từ [@BotFather](https://t.me/BotFather) |
| `TELEGRAM_STORAGE_CHANNEL_ID` | ID channel lưu video (dạng `-100xxxxxxxxxx`), bot phải là admin |
| `TELEGRAM_WEBHOOK_BASE_URL` | URL public của service (ví dụ domain Render) |
| `TELEGRAM_WEBHOOK_SECRET_TOKEN` | Chuỗi bí mật ngẫu nhiên, dùng để Telegram xác thực webhook request |
| `DATABASE_URL` | Connection string Supabase Postgres (xem mục Supabase bên dưới) |

### 4. Lấy Channel ID

- Thêm bot vào channel với quyền admin.
- Forward một tin nhắn từ channel tới [@userinfobot](https://t.me/userinfobot) hoặc dùng API `getChat` để lấy ID (dạng số âm, bắt đầu bằng `-100`).

## Chức năng người dùng (bổ sung ngoài 7-phase gốc)

Spec ban đầu liệt kê đầy đủ "Chức năng người dùng" nhưng không có phase riêng cho handler phía user — phần này được bổ sung sau Phase 6 để bot thực sự dùng được cho user thường, không chỉ admin.

| Lệnh/Nút | Mô tả |
|---|---|
| `/start` | Đăng ký + hiện menu chính |
| `/menu` | Mở lại Trang chủ |
| 🆕 Video mới | Series mới nhất |
| 🔥 Nổi bật | Series is_featured |
| 🏷️ Thể loại | Duyệt theo category |
| 🔎 Tìm kiếm | Tìm theo tên/tác giả/tag (gần đúng) |
| ▶️ Tiếp tục xem | WatchProgress chưa hoàn thành |
| 🕘 Lịch sử | History, có phân trang |
| ❤️ Yêu thích | Series đang theo dõi, có nút theo dõi/bỏ theo dõi |
| 👤 Tài khoản | Thời gian xem, trạng thái VIP |

**Lưu ý:** nút phân trang "Sau/Trước" ở màn Tìm kiếm và Tiếp tục xem hiện chưa nối handler (không crash, chỉ chưa phản hồi) — vì 2 luồng này thường đủ ngắn để không cần phân trang, nhưng cần bổ sung nếu catalog lớn.

Toàn bộ luồng xem video (mọi nút ▶️) đi qua `PlaybackService`, đảm bảo `View`, `History`, và view-count của Video/Series luôn được ghi đồng bộ dù bấm từ bất kỳ màn nào (browse, search, favorites, history).

## Lệnh Admin (Phase 5)

Chỉ user có `telegram_id` nằm trong `ADMIN_IDS` mới dùng được các lệnh này (chặn bởi `IsAdminFilter`):

| Lệnh | Mô tả |
|---|---|
| `/admin` | Mở menu admin (inline keyboard) |
| `/add_video` | Bắt đầu luồng thêm video (forward từ channel → title → mô tả → thể loại) |
| `/create_series` | Tạo series/playlist mới |
| `/categories` | Xem danh sách thể loại |
| `/add_category` | Thêm thể loại mới |
| `/users [offset]` | Xem danh sách user (phân trang) |
| `/ban <telegram_id> [lý do]` | Khóa user |
| `/unban <telegram_id>` | Mở khóa user |
| `/vip <telegram_id>` | Cấp VIP vĩnh viễn |
| `/unvip <telegram_id>` | Gỡ VIP |
| `/broadcast` | Soạn và gửi tin nhắn tới toàn bộ user (có xác nhận trước khi gửi) |
| `/dashboard` | Xem thống kê tổng quan (user, series, video, tổng lượt xem) |
| `/top_videos` | Top 10 video theo lượt xem (7 ngày qua) |
| `/top_series` | Top 10 series (ưu tiên featured, sau đó theo total_views) |
| `/top_viewers` | Top 10 người xem nhiều nhất (7 ngày qua) |
| `/views_chart` | Lượt xem theo từng ngày (7 ngày qua) |
| `/export_series` | Xuất toàn bộ series ra file CSV |
| `/import_series` | Hướng dẫn import series từ CSV (gửi kèm file .csv với caption `/import_series`) |

## Cấu hình Supabase

1. Tạo project mới tại [supabase.com](https://supabase.com).
2. Vào **Project Settings → Database → Connection string**.
3. Dùng **Connection Pooling** (transaction mode, cổng `6543`) cho `DATABASE_URL` của app khi chạy production (phù hợp với môi trường serverless/nhiều instance như Render).
4. Dùng **Direct connection** (cổng `5432`) khi chạy Alembic migration cục bộ nếu pooler không hỗ trợ statement cần thiết.
5. Format: `postgresql+asyncpg://postgres:<password>@<host>:<port>/postgres`

> Alembic migrations sẽ được thêm từ Phase 2 (bảng `users` là bảng đầu tiên).

## Cấu hình Telegram Webhook

Bot **không dùng polling** — bắt buộc dùng webhook. Ứng dụng tự động gọi `setWebhook` khi khởi động (xem `app/main.py`, hàm `lifespan`) và `deleteWebhook` khi tắt.

- Endpoint webhook: `POST {TELEGRAM_WEBHOOK_BASE_URL}{TELEGRAM_WEBHOOK_PATH}` (mặc định `/webhook/telegram`)
- Mọi request được xác thực qua header `X-Telegram-Bot-Api-Secret-Token`, phải khớp `TELEGRAM_WEBHOOK_SECRET_TOKEN`.
- Health check: `GET /health`

## Chạy local với Docker Compose

```bash
docker compose up --build
```

Việc này sẽ khởi động:
- `app` — bot + FastAPI server (cổng `8000`)
- `db` — Postgres 16 local (dùng thay Supabase khi dev offline; đổi `DATABASE_URL` trong `.env` để dùng Supabase trực tiếp)
- `redis` — chỉ chạy khi bật profile: `docker compose --profile redis up`

## Chạy test / lint

```bash
ruff check app tests
black --check app tests
pytest
```

`pytest` chạy toàn bộ unit test (SQLite in-memory, nhanh) **và** integration test trong `tests/integration/` — integration test tự động **skip** nếu `DATABASE_URL` không trỏ tới Postgres khả dụng (mặc định khi chạy local không có Docker). Để thực sự chạy integration test (verify toàn bộ migration chain + hành vi riêng của Postgres như ILIKE, BigInteger), khởi động Postgres local rồi trỏ `DATABASE_URL` vào đó:

```bash
docker compose up -d db
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
pytest tests/integration/ -v
```

Trên GitHub Actions CI, integration test luôn chạy thật vì CI có sẵn Postgres service (xem `.github/workflows/ci.yml`).

## Deploy lên Render (Phase 7 — chi tiết từng bước)

### Bước 1 — Chuẩn bị Supabase trước khi deploy

1. Tạo project Supabase (nếu chưa có) và lấy **Connection Pooling** URI (transaction mode, cổng `6543`) từ **Project Settings → Database → Connection string**.
2. Chạy migration lên Supabase **từ máy local** trước (Render không tự chạy Alembic khi deploy):
   ```bash
   export DATABASE_URL="postgresql+asyncpg://postgres:<password>@<host>:6543/postgres"
   alembic upgrade head
   ```
   Xác nhận bằng cách kiểm tra bảng trong Supabase Table Editor — phải thấy đủ 12 bảng (`users`, `categories`, `series`, `videos`, `episodes`, `favorites`, `history`, `watch_progress`, `settings`, `notifications`, `views`, `alembic_version`).

### Bước 2 — Push code lên GitHub

Render build trực tiếp từ Git repo (GitHub/GitLab/Bitbucket) — không build được từ file zip tải về. Push toàn bộ project (bao gồm `render.yaml` ở root) lên repo GitHub của bạn.

### Bước 3 — Tạo Blueprint trên Render

1. Đăng nhập [Render Dashboard](https://dashboard.render.com), bấm **New → Blueprint**.
2. Nếu chưa từng liên kết GitHub, Render sẽ yêu cầu cấp quyền truy cập — chọn repo `telegram-video-platform` (hoặc tên bạn đặt).
3. Render tự đọc file `render.yaml` ở root repo và hiển thị preview service sẽ được tạo (đã cấu hình sẵn: `runtime: docker`, `healthCheckPath: /health`, tự sinh `TELEGRAM_WEBHOOK_SECRET_TOKEN`).
4. Vì `render.yaml` khai báo `sync: false` cho các biến nhạy cảm, Render sẽ hiện form yêu cầu bạn điền trực tiếp (không qua URL, không lộ secret):
   - `TELEGRAM_BOT_TOKEN` — từ @BotFather
   - `TELEGRAM_STORAGE_CHANNEL_ID` — dạng `-100xxxxxxxxxx`
   - `DATABASE_URL` — Connection Pooling URI Supabase (giống Bước 1)
   - `ADMIN_IDS` — telegram_id của bạn
   - `TELEGRAM_WEBHOOK_BASE_URL` — để tạm trống, sẽ điền ở Bước 5
5. Bấm **Deploy Blueprint**.

### Bước 4 — Theo dõi build

Render build image theo `Dockerfile` (multi-stage, đã tối ưu sẵn từ Phase 1) rồi khởi động container. Theo dõi log ở trang Service — lỗi thường gặp là thiếu biến môi trường bắt buộc, Pydantic Settings sẽ báo lỗi rõ ràng ngay khi container khởi động.

### Bước 5 — Cập nhật webhook URL và xác nhận

1. Sau khi deploy thành công, Render cấp domain dạng `https://telegram-video-platform-xxxx.onrender.com`.
2. Vào **Environment** của Service, cập nhật biến `TELEGRAM_WEBHOOK_BASE_URL` bằng domain thật này.
3. Lưu lại — Render **tự động redeploy** khi biến môi trường thay đổi (không cần bấm gì thêm), `setWebhook` sẽ tự chạy lại trong `lifespan` của FastAPI.
4. Kiểm tra `GET https://<domain>/health` trả về `{"status": "ok"}`.
5. Nhắn `/start` cho bot trên Telegram để xác nhận webhook nhận update thành công.

### Cập nhật code sau này

Mỗi lần push lên branch `main`, Render tự rebuild theo `autoDeployTrigger: commit` đã khai báo trong `render.yaml`. Nếu migration mới được thêm, luôn chạy `alembic upgrade head` từ local (trỏ vào Supabase) **trước khi** push code — ứng dụng không tự chạy migration khi khởi động.

### ⚠️ Free tier & cold start

Service Render **Free** tự động "ngủ" (spin down) sau **15 phút không có traffic**, và mất khoảng **30-60 giây** để khởi động lại khi có request mới. Vì bot dùng **webhook** (Telegram chủ động gọi tới bot, không phải bot chủ động hỏi), điều này có nghĩa:

- Nếu bot đang "ngủ", update đầu tiên từ Telegram sau thời gian im lặng có thể bị trễ hoặc thất bại do timeout.
- Free Postgres của Supabase cũng có cơ chế tạm dừng riêng sau thời gian dài không hoạt động (khác biệt với Render, xem tài liệu Supabase).

**Cách khắc phục miễn phí — ping định kỳ giữ service "thức":**

Dùng một dịch vụ cron miễn phí (ví dụ [cron-job.org](https://cron-job.org)) để gọi `GET https://<domain>/health` mỗi 10-14 phút. Vì endpoint `/health` không chạm database, chi phí gần như bằng 0 và giữ container luôn sẵn sàng.

**Cách khắc phục triệt để (trả phí):** nâng cấp Service lên plan `starter` trở lên trong `render.yaml` (`plan: starter`) — loại bỏ hoàn toàn cold start, ổn định hơn cho bot chạy 24/7 phục vụ nhiều user thật.


## Backup / Restore / Update

### Backup Supabase

- Supabase Free/Pro tier có **Point-in-Time Recovery** hoặc backup hàng ngày tùy gói — kiểm tra ở **Project Settings → Database → Backups**.
- Để backup thủ công bổ sung, dùng `pg_dump` định kỳ (ví dụ qua GitHub Actions scheduled workflow hoặc cron job riêng):
  ```bash
  pg_dump "postgresql://postgres:<password>@<host>:5432/postgres" -F c -f backup_$(date +%Y%m%d).dump
  ```
  Dùng connection **trực tiếp** (cổng `5432`), không dùng pooler, cho `pg_dump`.

### Restore

```bash
pg_restore -d "postgresql://postgres:<password>@<host>:5432/postgres" --clean --if-exists backup_YYYYMMDD.dump
```

### Update / Rollback migration

- Update: `alembic upgrade head` sau khi thêm revision mới, chạy trước khi push code lên Render (theo Bước 5 ở trên).
- Rollback 1 bước: `alembic downgrade -1`.
- Rollback về đầu (xóa toàn bộ schema): `alembic downgrade base` — chỉ dùng khi chắc chắn, vì mất toàn bộ dữ liệu.
- Render hỗ trợ **Rollback** (chọn deploy cũ trong lịch sử deploy của Service) để quay lại nhanh nếu code mới có lỗi runtime, độc lập với việc rollback migration.

## Troubleshooting

| Vấn đề | Nguyên nhân thường gặp |
|---|---|
| Webhook không nhận update | Sai `TELEGRAM_WEBHOOK_BASE_URL`, hoặc secret token không khớp, hoặc bot chưa có quyền trong channel |
| `401 Unauthorized` ở `/webhook/telegram` | Header `X-Telegram-Bot-Api-Secret-Token` sai — kiểm tra `TELEGRAM_WEBHOOK_SECRET_TOKEN` |
| Container không start | Kiểm tra thiếu biến môi trường bắt buộc (Pydantic Settings sẽ raise lỗi rõ ràng khi thiếu) |
| Không copy được video | Bot chưa là admin trong `TELEGRAM_STORAGE_CHANNEL_ID`, hoặc sai `message_id` |
| Lỗi `prepared statement ... already exists` (ngẫu nhiên, dưới tải cao) | Đang dùng Supabase Connection Pooling (pgbouncer) — đã được xử lý qua `statement_cache_size=0` trong `app/database/engine.py`, nhưng nếu tự thêm code khác dùng asyncpg trực tiếp, nhớ áp dụng tương tự |
| CI fail ở bước integration test | Kiểm tra Postgres service trong `ci.yml` có healthy không; hoặc migration mới viết tay bị sai cú pháp — chạy `alembic upgrade head` local trước khi push |
| Deploy Render thành công nhưng bot không phản hồi | `TELEGRAM_WEBHOOK_BASE_URL` chưa cập nhật đúng domain Render cấp — xem lại Bước 5 ở mục Deploy |
| Bot không phản hồi sau thời gian dài không dùng | Free tier Render đang "ngủ" (cold start ~30-60s) — xem mục "Free tier & cold start", thiết lập ping định kỳ hoặc nâng cấp plan |
| Migration mới không áp dụng lên Supabase sau khi deploy | Render không tự chạy Alembic — luôn chạy `alembic upgrade head` từ local trỏ vào Supabase trước khi push code |

## Lộ trình phát triển (Phases)

- [x] **Phase 1** — Khởi tạo project, Docker, Supabase config, Webhook
- [x] **Phase 2** — Authentication, Database, Users
- [x] **Phase 3** — Video, Categories, Series
- [x] **Phase 4** — Search, History, Favorite
- [x] **Phase 5** — Admin Panel
- [x] **Phase 6** — Statistics, Optimization
- [x] **Phase 7** — Deployment, Testing, CI/CD
