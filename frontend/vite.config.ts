import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  build: {
    target: 'es2020',
    chunkSizeWarningLimit: 1400, // MapLibre tek başına ~800 KB
    // Varlıklar data: URI olarak gömülmesin; CSP yazı tiplerine yalnızca 'self' izni veriyor.
    assetsInlineLimit: 0,
  },
  server: {
    port: 5174,
    strictPort: true,
    // Geliştirmede API yerel FastAPI sunucusundan gelir: uvicorn app.main:create_app --factory --port 8000
    proxy: { '/api': 'http://127.0.0.1:8000' },
  },
});
