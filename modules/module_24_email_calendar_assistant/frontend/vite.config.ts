import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5176,
    proxy: {
      '/api/v1/email-calendar': {
        target: 'http://127.0.0.1:8124',
        changeOrigin: true,
        ws: true,
      },
    },
  },
});
