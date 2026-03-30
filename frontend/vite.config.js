import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { copyFileSync, existsSync, mkdirSync, cpSync } from 'fs'
import { resolve } from 'path'

// Production (Vercel): landing at /, SPA at /app/ — see root vercel.json
// landing/index.html lives inside frontend/ so it works regardless of Vercel Root Directory setting
/** В dev base = '/', но документация ссылается на /app/... как в проде — отдаём тот же public-файл. */
const familyTreePreviewAlias = () => ({
  name: 'family-tree-preview-alias',
  configureServer(server) {
    server.middlewares.use((req, _res, next) => {
      if (req.url?.startsWith('/app/family-tree-connectors-preview.html')) {
        req.url =
          '/family-tree-connectors-preview.html' +
          req.url.slice('/app/family-tree-connectors-preview.html'.length)
      }
      next()
    })
  },
})

const landingToDist = () => ({
  name: 'copy-landing-to-dist-root',
  closeBundle() {
    const landingDir = resolve(__dirname, 'landing')
    const destDir = resolve(__dirname, 'dist')
    if (!existsSync(destDir)) mkdirSync(destDir, { recursive: true })
    copyFileSync(resolve(landingDir, 'index.html'), resolve(destDir, 'index.html'))
    const imgs = resolve(landingDir, 'images')
    if (existsSync(imgs)) {
      const destImgs = resolve(destDir, 'images')
      cpSync(imgs, destImgs, { recursive: true })
    }
    console.log('[landing] copied to dist/index.html + images ✓')
  },
})

// https://vitejs.dev/config/
export default defineConfig(({ command }) => {
  const prodBuild = command === 'build'
  return {
    plugins: [react(), familyTreePreviewAlias(), ...(prodBuild ? [landingToDist()] : [])],
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

