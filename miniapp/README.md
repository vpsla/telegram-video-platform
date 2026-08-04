# Telegram Mini App — Video Platform

Frontend đơn giản (React + Vite) chạy bên trong Telegram, gọi REST API từ backend FastAPI đã có sẵn.

## Tính năng (Mức 1)

- 🏠 **Trang chủ** — series mới nhất + nổi bật
- 🔎 **Tìm kiếm** — tìm theo tên/tác giả/tag, debounce 400ms
- 🕘 **Lịch sử** — video đã xem + tiếp tục xem
- 👤 **Tài khoản** — thời gian xem, trạng thái VIP
- 📖 **Chi tiết series** — danh sách tập, bấm play gửi video qua bot

## Cách hoạt động

1. User bấm nút "🌐 Mở Mini App" trong bot → Telegram mở webview load trang này
2. Trang gọi REST API (`/api/v1/...`) trên backend Render để lấy dữ liệu
3. Khi user bấm ▶️ vào 1 tập, Mini App gọi `Telegram.WebApp.sendData()` gửi `video_id` về bot
4. Bot nhận qua `web_app_data` handler → gọi `PlaybackService` → `copyMessage` gửi video vào chat

> Mini App **chỉ duyệt/tìm kiếm** — việc gửi video luôn qua bot (đúng nguyên tắc `copyMessage`, không tải lại video).

## Cài đặt local

```bash
cd miniapp
npm install
npm run dev
```

Mở `http://localhost:5173` — chạy ở chế độ "dev mode" (không có Telegram context, dùng `alert()` thay vì gửi video thật).

## Cấu hình API URL

Sửa file `.env` trong `miniapp/` (tạo mới nếu chưa có):
```
VITE_API_URL=https://telegram-video-platform.onrender.com
```

## Build production

```bash
npm run build
```
Output ở `miniapp/dist/`.

## Deploy lên GitHub Pages (miễn phí)

### Cách 1 — Tự động qua GitHub Actions (khuyến nghị)

1. Vào repo GitHub → **Settings → Pages**
2. Ở **Source**, chọn **GitHub Actions**
3. Vào **Settings → Secrets and variables → Actions → Variables**
4. Thêm variable `MINIAPP_API_URL` = domain Render của bạn (ví dụ `https://telegram-video-platform.onrender.com`)
5. Push code lên `main` (workflow `.github/workflows/deploy-miniapp.yml` tự chạy khi có thay đổi trong `miniapp/`)
6. Sau khi deploy xong, Mini App có tại: `https://YOUR-USERNAME.github.io/YOUR-REPO/`

### Cách 2 — Deploy thủ công

```bash
cd miniapp
npm run build
npx gh-pages -d dist
```

## Đăng ký Mini App URL với bot

1. Copy URL Mini App (`https://YOUR-USERNAME.github.io/YOUR-REPO/`)
2. Vào **Render → Environment**
3. Điền biến `TELEGRAM_MINIAPP_URL` = URL đó
4. Save Changes → Render tự redeploy

Sau đó nút "🌐 Mở Mini App" sẽ xuất hiện trong menu `/start` và `/menu` của bot.

## Cấu hình BotFather (khuyến nghị)

Để Mini App mở đẹp hơn (có nút riêng cạnh thanh nhập tin nhắn):

1. Nhắn [@BotFather](https://t.me/BotFather) → `/mybots` → chọn bot → **Bot Settings → Menu Button**
2. Chọn **Configure menu button**
3. Nhập URL Mini App
4. Đặt tên nút, ví dụ: `Xem video`

## Lưu ý về `vite.config.js`

`base: "/telegram-video-platform/"` phải khớp với tên repo GitHub thật. Nếu repo tên khác, sửa lại giá trị này trước khi build — nếu không CSS/JS sẽ load sai đường dẫn (trang trắng).
