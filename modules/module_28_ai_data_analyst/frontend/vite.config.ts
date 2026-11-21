import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5128,
    proxy: {
      '/api/v1/ai-data-analyst': {
        target: 'http://127.0.0.1:8128',
        changeOrigin: true,
        ws: true,
      },
    },
  },
});
