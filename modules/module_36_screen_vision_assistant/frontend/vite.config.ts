import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5136,
    proxy: {
      "/api/v1/vision": {
        target: "http://127.0.0.1:8136",
        changeOrigin: true,
        ws: true
      }
    }
  }
});
