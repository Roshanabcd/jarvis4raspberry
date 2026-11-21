import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5137,
    proxy: {
      "/api/v1/devices": {
        target: "http://127.0.0.1:8137",
        changeOrigin: true,
        ws: true
      }
    }
  }
});
