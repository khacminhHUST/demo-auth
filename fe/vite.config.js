import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const apiTarget = 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    // Proxy API sang backend qua CÙNG origin với frontend, để cookie refresh_token
    // luôn là first-party (khác port = khác origin = trình duyệt hiện đại coi là
    // third-party cookie và chặn, dù SameSite đã đúng).
    proxy: {
      '/auth': { target: apiTarget, changeOrigin: true },
      '/password': { target: apiTarget, changeOrigin: true },
      '/users': { target: apiTarget, changeOrigin: true, ws: false },
      '/health': { target: apiTarget, changeOrigin: true },
    },
  },
})
