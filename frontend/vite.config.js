import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    // Backend (FastAPI) runs on :8000 — see backend/README.md
    proxy: { "/api": "http://localhost:8000" },
  },
});
