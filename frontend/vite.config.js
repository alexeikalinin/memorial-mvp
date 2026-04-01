import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { createReadStream, copyFileSync, readFileSync, writeFileSync, existsSync, mkdirSync, cpSync, statSync } from 'fs'
import { resolve, basename } from 'path'
import { fileURLToPath } from 'url'

const __dirname = fileURLToPath(new URL('.', import.meta.url))

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

/** Раздача /video/* из frontend/landing/video в dev (с Range для seek). */
const landingVideoDev = () => ({
  name: 'landing-video-dev',
  configureServer(server) {
    server.middlewares.use((req, res, next) => {
      if (!req.url?.startsWith('/video/')) return next()
      const raw = req.url.slice('/video/'.length).split('?')[0]
      const name = basename(decodeURIComponent(raw))
      if (!name) return next()
      const file = resolve(__dirname, 'landing/video', name)
      if (!existsSync(file)) return next()
      const size = statSync(file).size
      const range = req.headers.range
      res.setHeader('Accept-Ranges', 'bytes')
      res.setHeader('Content-Type', 'video/mp4')
      if (range) {
        const m = /^bytes=(\d*)-(\d*)$/.exec(range)
        if (!m) {
          res.statusCode = 416
          res.end()
          return
        }
        let start = m[1] !== '' ? parseInt(m[1], 10) : 0
        let end = m[2] !== '' ? parseInt(m[2], 10) : size - 1
        if (Number.isNaN(start) || Number.isNaN(end) || start > end || start >= size) {
          res.statusCode = 416
          res.end()
          return
        }
        end = Math.min(end, size - 1)
        const chunkSize = end - start + 1
        res.statusCode = 206
        res.setHeader('Content-Range', `bytes ${start}-${end}/${size}`)
        res.setHeader('Content-Length', chunkSize)
        createReadStream(file, { start, end }).pipe(res)
      } else {
        res.setHeader('Content-Length', size)
        createReadStream(file).pipe(res)
      }
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
    const vid = resolve(landingDir, 'video')
    if (existsSync(vid)) {
      const destVid = resolve(destDir, 'video')
      cpSync(vid, destVid, { recursive: true })
    }
    const destIndex = resolve(destDir, 'index.html')
    if (existsSync(destIndex)) {
      const api = process.env.VITE_LANDING_API_URL || process.env.VITE_API_URL || ''
      let html = readFileSync(destIndex, 'utf8')
      html = html.replace('__INJECT_LANDING_API__', JSON.stringify(api))
      writeFileSync(destIndex, html)
    }
    console.log('[landing] copied to dist/index.html + images + video ✓ (API base injected)')
  },
})

// https://vitejs.dev/config/
export default defineConfig(({ command }) => {
  const prodBuild = command === 'build'
  return {
    plugins: [
      react(),
      familyTreePreviewAlias(),
      landingVideoDev(),
      ...(prodBuild ? [landingToDist()] : []),
    ],
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

