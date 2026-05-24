import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const backendUrl = process.env.VITE_BACKEND_URL ?? `http://127.0.0.1:${process.env.APP_PORT ?? '8787'}`;
const host = process.env.VITE_HOST ?? '0.0.0.0';
const port = Number(process.env.VITE_PORT ?? 5173);

export default defineConfig({
  plugins: [react()],
  server: {
    host,
    port,
    proxy: {
      '/api': {
        target: backendUrl,
        changeOrigin: true
      }
    }
  }
});