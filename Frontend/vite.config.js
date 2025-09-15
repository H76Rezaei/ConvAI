import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
  
  // Server config for development
  server: {
    port: 5173,
    host: true,
  },
       
  preview: {
    port: 4173,
    host: true,
  },

  // Test configuration for Vitest
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.js',
    mockReset: true,
    clearMocks: true,
  },
})