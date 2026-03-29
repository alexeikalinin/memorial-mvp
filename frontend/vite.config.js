import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { copyFileSync } from 'fs'
import { resolve } from 'path'

// Production (Vercel): landing at /, SPA at /app/ — see root vercel.json
const landingToDist = () => ({
  name: 'copy-landing-to-dist-root',
  closeBundle() {
    copyFileSync(
      resolve(__dirname, '../landing/index.html'),
      resolve(__dirname, 'dist/index.html')
    )
  },
})

// https://vitejs.dev/config/
export default defineConfig(({ command }) => {
  const prodBuild = command === 'build'
  return {
    plugins: [react(), ...(prodBuild ? [landingToDist()] : [])],
    base: prodBuild ? '/app/' : '/',
    build: prodBuild ? { outDir: 'dist/app', emptyOutDir: true } : undefined,
    server: {
      port: 5173,
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
  }
})

