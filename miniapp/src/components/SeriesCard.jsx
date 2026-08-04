export default function SeriesCard({ series, onClick }) {
  return (
    <div className="series-card" onClick={() => onClick(series.id)}>
      <div className="series-thumb">
        {series.thumbnail_file_id ? "🎬" : "📖"}
      </div>
      <div className="series-info">
        <div className="series-title">{series.title}</div>
        <div className="series-meta">
          <span>👁 {series.total_views}</span>
          <span>🎬 {series.episode_count} tập</span>
        </div>
      </div>
    </div>
  );
}
