import { useState, useEffect } from "react";
import { api } from "../api.js";
import SeriesCard from "../components/SeriesCard.jsx";

export default function HomePage({ onOpenSeries }) {
  const [newest, setNewest] = useState([]);
  const [featured, setFeatured] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.getNewest(), api.getFeatured()])
      .then(([n, f]) => {
        setNewest(n.items || []);
        setFeatured(f.items || []);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="spinner" />;

  return (
    <div>
      {featured.length > 0 && (
        <>
          <div className="section-title">🔥 Nổi bật</div>
          <div className="series-grid">
            {featured.slice(0, 4).map((s) => (
              <SeriesCard key={s.id} series={s} onClick={onOpenSeries} />
            ))}
          </div>
        </>
      )}

      <div className="section-title">🆕 Mới cập nhật</div>
      {newest.length === 0 ? (
        <div className="empty">Chưa có nội dung nào</div>
      ) : (
        <div className="series-grid">
          {newest.map((s) => (
            <SeriesCard key={s.id} series={s} onClick={onOpenSeries} />
          ))}
        </div>
      )}
    </div>
  );
}
