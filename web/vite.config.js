import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
  plugins: [svelte()],
  base: '/myaddon/',  // Critical for asset paths
  build: {
    outDir: 'dist',    // Output to web/dist
    emptyOutDir: true  // Clear dist on build
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8188',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
});