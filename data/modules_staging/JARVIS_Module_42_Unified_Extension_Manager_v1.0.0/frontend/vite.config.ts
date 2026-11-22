import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5142,
    proxy: {
      "/api/v1/extensions": {
        target: "http://127.0.0.1:8142",
        changeOrigin: true,
        ws: true
      }
    }
  }
});
