import { useState, useEffect } from 'react'
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
}) {
  const [blobUrl, setBlobUrl] = useState(null)
  const [failed, setFailed] = useState(false)

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
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [mediaId, thumbnail, directUrl])

  if (directUrl) {
    return <img src={directUrl} alt={alt} className={className} />
  }

  if (!mediaId || failed) return fallback

  if (!blobUrl) {
    return (
      <span
        className={`api-media-image-loading ${className}`.trim()}
        aria-hidden
        style={{
          display: 'block',
          width: '100%',
          height: '100%',
          minHeight: '48px',
          background: 'linear-gradient(135deg, var(--surface-warm, #f5f0e8) 0%, var(--border, #e8e0d4) 100%)',
        }}
      />
    )
  }

  return <img src={blobUrl} alt={alt} className={className} />
}
