import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/auth': 'http://localhost:8765',
      '/leaderboard': 'http://localhost:8765',
      '/ws': {
        target: 'ws://localhost:8765',
        ws: true,
      },
    },
  },
})
