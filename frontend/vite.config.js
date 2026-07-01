import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The dev server proxies /api to the FastAPI backend so the frontend can use
// same-origin relative URLs (no CORS headaches in development).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: process.env.HINDSIGHT_API || "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
