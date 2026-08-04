import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  // Set base path cho GitHub Pages: https://USERNAME.github.io/REPO-NAME/
  // Đổi "/telegram-video-platform/" thành "/" nếu deploy ở domain riêng
  base: "/telegram-video-platform/",
  build: {
    outDir: "dist",
  },
});
