import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5131,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8131",
        changeOrigin: true,
        ws: true
      }
    }
  }
});
