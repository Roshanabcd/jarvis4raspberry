import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5135,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8135",
        changeOrigin: true,
        ws: true
      }
    }
  }
});
