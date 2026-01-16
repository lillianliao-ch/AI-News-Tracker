import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import tailwind from '@astrojs/tailwind';

export default defineConfig({
  integrations: [
    react(),
    tailwind()
  ],
  vite: {
    build: {
      // 优化构建
      rollupOptions: {
        output: {
          manualChunks: {
            'react': ['react', 'react-dom'],
            'vendor': ['@astrojs/react']
          }
        }
      }
    }
  }
});
