import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5140,
    proxy: {
      "/api/v1/approvals": {
        target: "http://127.0.0.1:8140",
        changeOrigin: true,
        ws: true
      }
    }
  }
});
