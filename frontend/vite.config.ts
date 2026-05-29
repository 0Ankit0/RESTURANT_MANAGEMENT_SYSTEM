import path from 'node:path';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  envPrefix: ['VITE_', 'NEXT_PUBLIC_'],
  resolve: {
    alias: [
      { find: '@', replacement: path.resolve(__dirname, './src') },
    ],
  },
  define: {
    'process.env': 'import.meta.env',
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api/v1': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  preview: {
    host: '0.0.0.0',
    port: 3000,
  },
  build: {
    cssCodeSplit: true,
    modulePreload: {
      polyfill: true,
    },
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return;

          if (id.includes('react-router')) {
            return 'vendor-router';
          }

          if (id.includes('react-dom') || id.includes('/react/')) {
            return 'vendor-react';
          }

          if (id.includes('@tanstack/react-query') || id.includes('zustand')) {
            return 'vendor-state';
          }

          if (id.includes('react-hook-form') || id.includes('@hookform/resolvers') || id.includes('/zod/')) {
            return 'vendor-forms';
          }

          if (id.includes('firebase') || id.includes('posthog-js') || id.includes('mixpanel-browser')) {
            return 'vendor-analytics';
          }

          if (id.includes('lucide-react')) {
            return 'vendor-icons';
          }

          return 'vendor-misc';
        },
      },
    },
  },
});
