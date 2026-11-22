import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5143,
    proxy: {
      "/api/v1/screen-guardian": {
        target: "http://127.0.0.1:8143",
        changeOrigin: true,
        ws: true
      }
    }
  }
});
