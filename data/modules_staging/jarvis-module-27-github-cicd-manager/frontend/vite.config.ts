import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5127,
    proxy: {
      '/api/v1/github-cicd': {
        target: 'http://127.0.0.1:8127',
        changeOrigin: true,
        ws: true,
      },
    },
  },
});
