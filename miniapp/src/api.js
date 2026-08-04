// API client cho backend Render
// Đổi BASE_URL thành domain Render thật của bạn
const BASE_URL = import.meta.env.VITE_API_URL || "https://telegram-video-platform.onrender.com";

let _initData = "";

export function setInitData(initData) {
  _initData = initData;
}

async function request(path, params = {}) {
  const url = new URL(`${BASE_URL}/api/v1${path}`);

  // Thêm init_data vào mọi request (dùng cho các endpoint cần auth)
  if (_initData) {
    url.searchParams.set("init_data", _initData);
  }

  // Thêm các param khác
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined) url.searchParams.set(k, v);
  });

  const res = await fetch(url.toString());
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  // Public endpoints (không cần auth)
  getNewest: (offset = 0) => request("/series/newest", { offset, limit: 20 }),
  getFeatured: (offset = 0) => request("/series/featured", { offset, limit: 20 }),
  search: (q, offset = 0) => request("/series/search", { q, offset, limit: 20 }),
  getSeriesDetail: (id) => request(`/series/${id}`),
  getCategories: () => request("/categories"),
  getCategorySeries: (id, offset = 0) =>
    request(`/categories/${id}/series`, { offset, limit: 20 }),

  // Endpoints cần auth (init_data)
  getHistory: (offset = 0) => request("/history", { offset, limit: 20 }),
  getContinueWatching: () => request("/continue-watching"),
  getMe: () => request("/me"),
};
