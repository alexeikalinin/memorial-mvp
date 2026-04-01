import { useState, useEffect, useRef } from 'react'
import apiClient from '../api/client'

/**
 * Картинка из /media/:id через axios (тот же baseURL и Bearer, что и API).
 * Обычный <img src="/api/v1/media/..."> на проде (Vercel) без VITE_API_URL
 * попадает в SPA и ломается; blob-загрузка совпадает с поведением остальных запросов.
 */
export default function ApiMediaImage({
  mediaId,
  thumbnail = null,
  directUrl = null,
  alt = '',
  className = '',
  fallback = null,
  loading = 'lazy',
  eager = false,
}) {
  const [blobUrl, setBlobUrl] = useState(null)
  const [failed, setFailed] = useState(false)
  const [shouldLoad, setShouldLoad] = useState(Boolean(eager || directUrl))
  const hostRef = useRef(null)

  // Reuse fetched blobs between renders/pages during a session.
  const cacheKey = directUrl ? null : `${mediaId || 'none'}|${thumbnail || 'orig'}`

  useEffect(() => {
    if (eager || directUrl) {
      setShouldLoad(true)
      return undefined
    }
    const el = hostRef.current
    if (!el) return undefined
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          setShouldLoad(true)
          observer.disconnect()
        }
      },
      { rootMargin: '200px 0px' }
    )
    observer.observe(el)
    return () => observer.disconnect()
  }, [eager, directUrl])

  useEffect(() => {
    if (directUrl) {
      setBlobUrl(null)
      setFailed(false)
      return undefined
    }
    if (!mediaId) {
      setFailed(true)
      return undefined
    }
    if (!shouldLoad) return undefined

    const cache = window.__apiMediaBlobCache || (window.__apiMediaBlobCache = new Map())
    if (cacheKey && cache.has(cacheKey)) {
      setBlobUrl(cache.get(cacheKey))
      setFailed(false)
      return undefined
    }

    let cancelled = false
    let objectUrl = null

    const load = async () => {
      try {
        const res = await apiClient.get(`/media/${mediaId}`, {
          params: thumbnail ? { thumbnail } : undefined,
          responseType: 'blob',
        })
        if (cancelled) return
        objectUrl = URL.createObjectURL(res.data)
        if (cacheKey) cache.set(cacheKey, objectUrl)
        setBlobUrl(objectUrl)
        setFailed(false)
      } catch {
        if (!cancelled) {
          setFailed(true)
          setBlobUrl(null)
        }
      }
    }

    load()
    return () => {
      cancelled = true
      // Keep cached URLs alive for session-level reuse.
      if (objectUrl && (!cacheKey || !(window.__apiMediaBlobCache?.has(cacheKey)))) {
        URL.revokeObjectURL(objectUrl)
      }
    }
  }, [mediaId, thumbnail, directUrl, shouldLoad, cacheKey])

  if (directUrl) {
    return (
      <img
        src={directUrl}
        alt={alt}
        className={className}
        loading={loading}
        decoding="async"
        fetchPriority={loading === 'eager' ? 'high' : 'low'}
      />
    )
  }

  if (!mediaId || failed) return fallback

  if (!blobUrl) {
    return (
      <span
        ref={hostRef}
        className={`api-media-image-loading ${className}`.trim()}
        aria-hidden
        style={{
          display: 'block',
          background:
            'linear-gradient(135deg, var(--surface-warm, #f5f0e8) 0%, var(--border, #e8e0d4) 100%)',
        }}
      />
    )
  }

  return (
    <img
      ref={hostRef}
      src={blobUrl}
      alt={alt}
      className={className}
      loading={loading}
      decoding="async"
      fetchPriority={loading === 'eager' ? 'high' : 'low'}
    />
  )
}
