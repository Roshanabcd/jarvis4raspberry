import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5125,
    proxy: {
      '/api/v1/meeting-assistant': {
        target: 'http://127.0.0.1:8125',
        changeOrigin: true,
        ws: true,
      },
    },
  },
});
