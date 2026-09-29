import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'node:url'

const here = fileURLToPath(new URL('.', import.meta.url))

// https://vitejs.dev/config/
export default defineConfig({
  root: here,
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
      '/ready': 'http://localhost:8000',
      '/metrics': 'http://localhost:8000',
    }
  },
  test: {
    root: here,
    environment: 'jsdom',
    globals: true,
    setupFiles: [fileURLToPath(new URL('./tests/setup.ts', import.meta.url))]
  }
} as any)
