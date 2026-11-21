import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5139,
    proxy: {
      "/api/v1/backups": {
        target: "http://127.0.0.1:8139",
        changeOrigin: true,
        ws: true
      }
    }
  }
});
