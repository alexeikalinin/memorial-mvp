import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { copyFileSync, existsSync, mkdirSync } from 'fs'
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
    const src = resolve(__dirname, 'landing/index.html')
    const destDir = resolve(__dirname, 'dist')
    const dest = resolve(destDir, 'index.html')
    if (!existsSync(destDir)) mkdirSync(destDir, { recursive: true })
    copyFileSync(src, dest)
    console.log('[landing] copied to dist/index.html ✓')
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

