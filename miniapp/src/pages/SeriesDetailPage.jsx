import { useState, useEffect } from "react";
import { api } from "../api.js";

function formatDuration(seconds) {
  if (!seconds) return "";
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

function sendVideoToBot(videoId) {
  // Gửi video_id lên bot qua Telegram WebApp sendData
  // Bot sẽ nhận và gửi copyMessage cho user
  const tg = window.Telegram?.WebApp;
  if (tg) {
    tg.sendData(JSON.stringify({ action: "watch", video_id: videoId }));
  } else {
    alert(`Dev mode: play video_id=${videoId}`);
  }
}

export default function SeriesDetailPage({ seriesId, onBack }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.getSeriesDetail(seriesId)
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [seriesId]);

  if (loading) return <div className="spinner" />;
  if (error) return <div className="empty">❌ {error}</div>;
  if (!data) return null;

  return (
    <div>
      <button className="back-btn" onClick={onBack}>
        ← Quay lại
      </button>

      <div className="detail-header">
        <div className="detail-cover">📖</div>
        <div className="detail-title">{data.title}</div>
        {data.author && (
          <div className="detail-desc">✍️ {data.author}</div>
        )}
        {data.description && (
          <div className="detail-desc">{data.description}</div>
        )}
        <div className="badges">
          {data.category_name && (
            <span className="badge">🏷️ {data.category_name}</span>
          )}
          {data.is_completed ? (
            <span className="badge">✅ Hoàn thành</span>
          ) : (
            <span className="badge">🔄 Đang tiến hành</span>
          )}
          <span className="badge">👁️ {data.total_views} lượt xem</span>
        </div>
      </div>

      <div className="section-title">
        📋 Danh sách tập ({data.episodes?.length || 0})
      </div>

      {data.episodes?.length === 0 ? (
        <div className="empty">Chưa có tập nào</div>
      ) : (
        <div className="episode-list">
          {data.episodes?.map((ep) => (
            <div
              key={ep.episode_number}
              className="episode-item"
              onClick={() => sendVideoToBot(ep.video_id)}
            >
              <div className="ep-number">{ep.episode_number}</div>
              <div className="ep-info">
                <div className="ep-title">{ep.title}</div>
                {ep.duration_seconds && (
                  <div className="ep-duration">
                    ⏱ {formatDuration(ep.duration_seconds)}
                  </div>
                )}
              </div>
              <div className="ep-play">▶️</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
