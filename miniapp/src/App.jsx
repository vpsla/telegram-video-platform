import { useState, useEffect } from "react";
import { setInitData } from "./api.js";
import HomePage from "./pages/HomePage.jsx";
import HistoryPage from "./pages/HistoryPage.jsx";
import SearchPage from "./pages/SearchPage.jsx";
import AccountPage from "./pages/AccountPage.jsx";
import SeriesDetailPage from "./pages/SeriesDetailPage.jsx";

const TABS = [
  { id: "home", icon: "🏠", label: "Trang chủ" },
  { id: "search", icon: "🔎", label: "Tìm kiếm" },
  { id: "history", icon: "🕘", label: "Lịch sử" },
  { id: "account", icon: "👤", label: "Tài khoản" },
];

export default function App() {
  const [tab, setTab] = useState("home");
  const [detail, setDetail] = useState(null); // { seriesId }
  const [tgReady, setTgReady] = useState(false);

  useEffect(() => {
    // Khởi tạo Telegram WebApp
    const tg = window.Telegram?.WebApp;
    if (tg) {
      tg.ready();
      tg.expand();
      // Set initData để gọi các API cần auth
      setInitData(tg.initData || "");
      setTgReady(true);
    } else {
      // Chạy ngoài Telegram (dev mode)
      setInitData("");
      setTgReady(true);
    }
  }, []);

  if (!tgReady) return <div className="loading">⏳</div>;

  // Xem chi tiết series (overlay toàn màn hình)
  if (detail) {
    return (
      <div className="app">
        <div className="page">
          <SeriesDetailPage
            seriesId={detail.seriesId}
            onBack={() => setDetail(null)}
          />
        </div>
      </div>
    );
  }

  const openSeries = (seriesId) => setDetail({ seriesId });

  return (
    <div className="app">
      <div className="page">
        {tab === "home" && <HomePage onOpenSeries={openSeries} />}
        {tab === "search" && <SearchPage onOpenSeries={openSeries} />}
        {tab === "history" && <HistoryPage />}
        {tab === "account" && <AccountPage />}
      </div>

      <nav className="nav">
        {TABS.map((t) => (
          <button
            key={t.id}
            className={`nav-btn ${tab === t.id ? "active" : ""}`}
            onClick={() => setTab(t.id)}
          >
            <span className="icon">{t.icon}</span>
            {t.label}
          </button>
        ))}
      </nav>
    </div>
  );
}
