import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5129,
    proxy: {
      '/api/v1/file-manager': {
        target: 'http://127.0.0.1:8129',
        changeOrigin: true,
        ws: true,
      },
    },
  },
});
