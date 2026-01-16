import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import tailwind from '@astrojs/tailwind';
import node from '@astrojs/node';

export default defineConfig({
  output: 'server',  // 启用 SSR
  adapter: node({
    mode: 'standalone'
  }),
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
    },
    define: {
      // 设置后端 API 地址
      'import.meta.env.PUBLIC_API_URL': JSON.stringify(
        process.env.PUBLIC_API_URL || 'https://ai-news-tracker-production-f7f4.up.railway.app'
      )
    }
  }
});

