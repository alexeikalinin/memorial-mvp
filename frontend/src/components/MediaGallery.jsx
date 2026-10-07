import { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import { createPortal } from 'react-dom'
import { memorialsAPI, getMediaUrl as getApiMediaUrl } from '../api/client'
import { useLanguage } from '../contexts/LanguageContext'
import ApiMediaImage from './ApiMediaImage'
import './MediaGallery.css'

function MediaGallery({ memorialId, onReload, coverPhotoId, onSetCover, canEdit = true, refreshKey }) {
  const { t } = useLanguage()
  const [media, setMedia] = useState([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState(null)
  const [viewerId, setViewerId] = useState(null)
  const uploadRef = useRef(null)
  const dialogRef = useRef(null)
  const closeRef = useRef(null)
  const touchRef = useRef(null)
  const photos = useMemo(() => media.filter(item => item.media_type === 'photo'), [media])
  const viewerIndex = photos.findIndex(item => item.id === viewerId)
  const viewerPhoto = photos[viewerIndex]
  const viewerOpen = Boolean(viewerPhoto)

  const loadMedia = useCallback(async () => {
    const response = await memorialsAPI.getMedia(memorialId)
    setMedia(Array.isArray(response.data) ? response.data : [])
  }, [memorialId])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    setViewerId(null)
    memorialsAPI.getMedia(memorialId).then(response => {
      if (!cancelled) setMedia(Array.isArray(response.data) ? response.data : [])
    }).catch(() => {
      if (!cancelled) { setMedia([]); setError({ key: 'media.load_error' }) }
    }).finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [memorialId, refreshKey])

  const movePhoto = useCallback((direction) => {
    setViewerId(current => {
      const index = photos.findIndex(item => item.id === current)
      return photos.length ? photos[(index + direction + photos.length) % photos.length].id : null
    })
  }, [photos])

  useEffect(() => {
    if (!viewerOpen) return undefined
    const previousFocus = document.activeElement
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    closeRef.current?.focus()
    const handleKey = event => {
      if (event.key === 'Escape') { event.preventDefault(); setViewerId(null) }
      if (event.key === 'ArrowLeft') { event.preventDefault(); movePhoto(-1) }
      if (event.key === 'ArrowRight') { event.preventDefault(); movePhoto(1) }
      if (event.key === 'Tab') {
        const controls = [...(dialogRef.current?.querySelectorAll('button:not([disabled]), [href], [tabindex="0"]') || [])]
        const first = controls[0]
        const last = controls[controls.length - 1]
        if (!controls.includes(document.activeElement)) { event.preventDefault(); first?.focus() }
        else if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus() }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus() }
      }
    }
    document.addEventListener('keydown', handleKey)
    return () => {
      document.removeEventListener('keydown', handleKey)
      document.body.style.overflow = previousOverflow
      if (previousFocus?.isConnected) previousFocus.focus()
    }
  }, [viewerOpen, movePhoto])

  const handleFileUpload = async event => {
    const input = event.target
    const files = Array.from(input.files || [])
    if (!files.length) return
    setUploading(true)
    setError(null)
    const failed = []
    let uploaded = 0
    for (const file of files) {
      try { await memorialsAPI.uploadMedia(memorialId, file); uploaded += 1 }
      catch { failed.push(file.name) }
    }
    if (failed.length) {
      setError({ key: 'media.upload_partial', params: { uploaded, total: files.length, files: failed.join(', ') } })
    }
    if (uploaded) {
      try { await loadMedia(); onReload?.() }
      catch { setError({ key: 'media.load_error' }) }
    }
    setUploading(false)
    input.value = ''
  }

  const handleDelete = async mediaId => {
    if (!window.confirm(t('media.delete_confirm'))) return
    try {
      await memorialsAPI.deleteMedia(memorialId, mediaId)
      await loadMedia()
      onReload?.()
    } catch {
      setError({ key: 'media.delete_error' })
    }
  }

  const mediaUrl = item => item.file_url || getApiMediaUrl(item.id)
  const uploadButton = label => (
    <button type="button" className="upload-btn" disabled={uploading} onClick={() => uploadRef.current?.click()}>
      {uploading ? t('media.uploading') : t(label)}
    </button>
  )

  if (loading) return <div className="loading">{t('media.loading')}</div>

  return (
    <div className="media-gallery">
      <div className="gallery-header">
        <h2>{t('media.title')}</h2>
        {canEdit && <div data-tour="media-upload">{uploadButton('media.upload')}</div>}
      </div>
      {canEdit && <input ref={uploadRef} type="file" multiple onChange={handleFileUpload} disabled={uploading} accept="image/*,video/*,audio/*" hidden />}
      {error && <p className="gallery-error" role="alert">{t(error.key, error.params)}</p>}
      {media.length === 0 ? (
        <div className="empty-state">
          <p>{t('media.empty')}</p>
          {canEdit && uploadButton('media.upload_first')}
        </div>
      ) : (
        <div className="gallery-grid">
          {media.map(item => (
            <div key={item.id} className="media-item">
              {item.media_type === 'photo' && (
                <button type="button" className="gallery-photo-open" onClick={() => setViewerId(item.id)} aria-label={t('media.viewer_open', { name: item.file_name || '' })}>
                  <ApiMediaImage mediaId={item.id} directUrl={item.file_url} thumbnail="medium" alt={item.file_name || ''} fallback={<div className="media-item-placeholder">{t('media.viewer_unavailable')}</div>} />
                </button>
              )}
              {item.media_type === 'video' && <video src={mediaUrl(item)} controls preload="metadata" playsInline />}
              {item.media_type === 'audio' && (
                <div className="audio-placeholder">
                  <span aria-hidden="true">♫</span>
                  <p>{item.file_name}</p>
                  <audio src={mediaUrl(item)} controls preload="metadata" aria-label={item.file_name} />
                </div>
              )}
              {coverPhotoId === item.id && <div className="cover-badge">{t('portraits.cover_badge')}</div>}
              {canEdit && (
                <div className="media-actions">
                  <div className="media-actions-left">
                    {item.media_type === 'photo' && onSetCover && <button type="button" className={`btn-cover${coverPhotoId === item.id ? ' active' : ''}`} onClick={() => onSetCover(item.id)}>{t('portraits.use_cover')}</button>}
                  </div>
                  <button type="button" className="btn-delete" onClick={() => handleDelete(item.id)} aria-label={t('media.delete_file_title')} title={t('media.delete_file_title')}>×</button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
      {viewerPhoto && createPortal(
        <div className="gallery-viewer-backdrop" onClick={event => { if (event.target === event.currentTarget) setViewerId(null) }}>
          <div className="gallery-viewer" role="dialog" aria-modal="true" aria-label={t('media.viewer_title')} ref={dialogRef}>
            <div className="gallery-viewer-toolbar">
              <span className="gallery-viewer-count" aria-live="polite">{t('media.viewer_count', { current: viewerIndex + 1, total: photos.length })}</span>
              <button type="button" className="gallery-viewer-close" ref={closeRef} aria-label={t('media.viewer_close')} onClick={() => setViewerId(null)}>×</button>
            </div>
            <div className="gallery-viewer-stage" onTouchStart={event => { const touch = event.touches[0]; touchRef.current = event.touches.length === 1 ? { x: touch.clientX, y: touch.clientY } : null }} onTouchEnd={event => {
              const start = touchRef.current
              touchRef.current = null
              const end = event.changedTouches[0]
              if (start && end && Math.abs(end.clientX - start.x) > 60 && Math.abs(end.clientX - start.x) > Math.abs(end.clientY - start.y)) movePhoto(end.clientX < start.x ? 1 : -1)
            }}>
              {photos.length > 1 && <button type="button" className="gallery-viewer-arrow previous" aria-label={t('media.viewer_previous')} onClick={() => movePhoto(-1)}>‹</button>}
              <ApiMediaImage key={viewerPhoto.id} mediaId={viewerPhoto.id} directUrl={viewerPhoto.file_url} alt={viewerPhoto.file_name || ''} eager loading="eager" fallback={<p className="gallery-viewer-unavailable">{t('media.viewer_unavailable')}</p>} />
              {photos.length > 1 && <button type="button" className="gallery-viewer-arrow next" aria-label={t('media.viewer_next')} onClick={() => movePhoto(1)}>›</button>}
            </div>
            <div className="gallery-viewer-footer"><span className="gallery-viewer-candle" aria-hidden="true"><i /></span><span>{viewerPhoto.file_name}</span></div>
          </div>
        </div>, document.body
      )}
    </div>
  )
}

export default MediaGallery
