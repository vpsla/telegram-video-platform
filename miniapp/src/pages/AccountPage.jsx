import { useState, useEffect } from "react";
import { api } from "../api.js";

function formatWatchTime(totalSeconds) {
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  if (hours > 0) return `${hours}h ${minutes}p`;
  return `${minutes} phút`;
}

export default function AccountPage() {
  const [me, setMe] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getMe()
      .then(setMe)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="spinner" />;

  if (error) {
    return (
      <div className="empty">
        ❌ Không thể tải thông tin tài khoản.
        <br />
        Vui lòng mở app từ trong Telegram.
      </div>
    );
  }

  if (!me) return null;

  return (
    <div>
      <div className="account-card">
        <div className="account-avatar">👤</div>
        <div className="account-name">{me.display_name}</div>
        <div className="account-sub">
          {me.is_vip ? "⭐ Thành viên VIP" : "Thành viên thường"}
        </div>
      </div>

      <div className="stats-row">
        <div className="stat-card">
          <div className="stat-value">{formatWatchTime(me.total_watch_seconds)}</div>
          <div className="stat-label">Thời gian xem</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">
            {new Date(me.joined_at).toLocaleDateString("vi-VN")}
          </div>
          <div className="stat-label">Ngày tham gia</div>
        </div>
      </div>
    </div>
  );
}
