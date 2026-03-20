import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    rollupOptions: {
      output: {
        // Add cache busting with hash to filenames
        entryFileNames: 'assets/[name]-[hash].js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]',

        manualChunks: (id) => {
          // Core React libraries
          if (id.includes('node_modules/react') || id.includes('node_modules/react-dom')) {
            return 'react-vendor';
          }

          // React Router
          if (id.includes('node_modules/react-router-dom')) {
            return 'router';
          }

          // Data fetching and state management
          if (id.includes('node_modules/@tanstack/react-query') || id.includes('node_modules/axios')) {
            return 'query';
          }

          // Radix UI components (large dependency)
          if (id.includes('node_modules/@radix-ui')) {
            return 'radix-ui';
          }

          // Date utilities (date-fns is large)
          if (id.includes('node_modules/date-fns')) {
            return 'date-utils';
          }

          // Lucide icons (large icon library)
          if (id.includes('node_modules/lucide-react')) {
            return 'icons';
          }

          // Chart libraries (recharts is heavy)
          if (id.includes('node_modules/recharts')) {
            return 'charts';
          }

          // Zustand (state management)
          if (id.includes('node_modules/zustand')) {
            return 'state';
          }

          // Other node_modules
          if (id.includes('node_modules')) {
            return 'vendor';
          }
        },
      },
    },
    // Enable CSS code splitting
    cssCodeSplit: true,

    // Optimize chunk size warnings (500KB uncompressed is reasonable with gzip)
    chunkSizeWarningLimit: 500,

    // Disable source maps in production (saves ~1.5MB), enable in dev
    sourcemap: false,

    // Minification
    minify: 'esbuild',

    // Target modern browsers for smaller bundles
    target: 'es2020',

    // Clear output directory before build to remove stale files
    emptyOutDir: true,

    // Optimize dependencies
    commonjsOptions: {
      include: [/node_modules/],
      transformMixedEsModules: true,
    },
  },

  // Development server optimization
  server: {
    // Enable HTTP/2 for faster dev loading
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
    // SPA fallback: serve index.html for all non-file requests (deep-link routing fix)
    // This is enabled by default in Vite, but explicit config ensures it works
    fs: {
      strict: false, // Allow serving files outside of root during development
    },
  },

  // Preview server configuration (production build preview)
  preview: {
    port: 4173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },

  // Ensure SPA fallback works - Vite handles this automatically but we're explicit
  appType: 'spa',
})
