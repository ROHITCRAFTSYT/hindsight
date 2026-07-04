import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The dev server proxies /api to the FastAPI backend so the frontend can use
// same-origin relative URLs (no CORS headaches in development).
export default defineConfig({
  plugins: [react()],
  server: {
    // PORT lets tooling (preview harnesses, CI) pick a free port; 5173 default.
    port: Number(process.env.PORT) || 5173,
    proxy: {
      "/api": {
        target: process.env.HINDSIGHT_API || "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
