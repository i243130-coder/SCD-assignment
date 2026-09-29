import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// https://vitejs.dev/config/
export default defineConfig({
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
    environment: 'jsdom',
    globals: true,
    root: __dirname,
    setupFiles: path.resolve(__dirname, 'tests/setup.ts')
  }
})
