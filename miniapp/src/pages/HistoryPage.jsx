import { useState, useEffect } from "react";
import { api } from "../api.js";

function timeAgo(isoString) {
  const diff = Date.now() - new Date(isoString).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "Vừa xong";
  if (mins < 60) return `${mins} phút trước`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} giờ trước`;
  const days = Math.floor(hours / 24);
  return `${days} ngày trước`;
}

export default function HistoryPage() {
  const [continuing, setContinuing] = useState([]);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([api.getContinueWatching(), api.getHistory()])
      .then(([c, h]) => {
        setContinuing(c.items || []);
        setHistory(h.items || []);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="spinner" />;
  if (error)
    return (
      <div className="empty">
        ❌ {error}
        <br />
        Mở app trong Telegram để xem lịch sử.
      </div>
    );

  return (
    <div>
      {continuing.length > 0 && (
        <>
          <div className="section-title">▶️ Tiếp tục xem</div>
          <div className="history-list">
            {continuing.map((item) => (
              <div key={item.video_id} className="history-item">
                <div className="history-icon">▶️</div>
                <div className="history-info">
                  <div className="history-title">{item.video_title}</div>
                  <div className="history-time">
                    Đã xem {Math.floor(item.position_seconds / 60)} phút
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      <div className="section-title">🕘 Lịch sử xem</div>
      {history.length === 0 ? (
        <div className="empty">Bạn chưa xem video nào</div>
      ) : (
        <div className="history-list">
          {history.map((item) => (
            <div key={item.id} className="history-item">
              <div className="history-icon">🎬</div>
              <div className="history-info">
                <div className="history-title">{item.video_title}</div>
                <div className="history-time">{timeAgo(item.watched_at)}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
