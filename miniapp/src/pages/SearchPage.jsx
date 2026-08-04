import { useState, useRef } from "react";
import { api } from "../api.js";
import SeriesCard from "../components/SeriesCard.jsx";

export default function SearchPage({ onOpenSeries }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const debounceRef = useRef(null);

  function handleChange(e) {
    const value = e.target.value;
    setQuery(value);

    clearTimeout(debounceRef.current);
    if (!value.trim()) {
      setResults([]);
      setSearched(false);
      return;
    }

    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      setSearched(true);
      try {
        const data = await api.search(value.trim());
        setResults(data.items || []);
      } catch (e) {
        console.error(e);
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 400);
  }

  return (
    <div>
      <div className="search-bar">
        <span>🔎</span>
        <input
          className="search-input"
          placeholder="Tìm theo tên, tác giả, tag..."
          value={query}
          onChange={handleChange}
          autoFocus
        />
      </div>

      {loading && <div className="spinner" />}

      {!loading && searched && results.length === 0 && (
        <div className="empty">Không tìm thấy kết quả cho "{query}"</div>
      )}

      {!loading && results.length > 0 && (
        <div className="series-grid">
          {results.map((s) => (
            <SeriesCard key={s.id} series={s} onClick={onOpenSeries} />
          ))}
        </div>
      )}

      {!searched && <div className="empty">Nhập từ khóa để tìm kiếm</div>}
    </div>
  );
}
