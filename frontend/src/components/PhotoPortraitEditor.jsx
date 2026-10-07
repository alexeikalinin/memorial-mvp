import { useEffect, useRef, useState } from 'react'
import apiClient, { memorialsAPI } from '../api/client'
import ApiMediaImage from './ApiMediaImage'
import { useLanguage } from '../contexts/LanguageContext'
import './PhotoPortraitEditor.css'

const FRAME = 300
const clamp = (value, bound) => Math.max(-bound, Math.min(bound, value))

export default function PhotoPortraitEditor({ memorial, kind, initialMediaId, onClose, onSaved }) {
  const { t } = useLanguage()
  const options = memorial.portrait_settings || {}
  const currentId = kind === 'avatar' ? options.avatar?.media_id || memorial.cover_photo_id : memorial.cover_photo_id
  const currentCrop = kind === 'avatar' ? options.avatar?.crop || (!options.avatar ? options.cover?.crop : null) : options.cover?.crop
  const [photos, setPhotos] = useState([])
  const [selected, setSelected] = useState(initialMediaId || currentId || null)
  const [sourceUrl, setSourceUrl] = useState(null)
  const [dimensions, setDimensions] = useState(null)
  const [rotation, setRotation] = useState(currentCrop?.rotation || 0)
  const [zoom, setZoom] = useState(1)
  const [pan, setPan] = useState({ x: 0, y: 0 })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const dialog = useRef(null)
  const [frameSize, setFrameSize] = useState(FRAME)
  const drag = useRef(null)
  const restoreCrop = useRef(!initialMediaId || initialMediaId === currentId ? currentCrop : null)

  useEffect(() => {
    const observer = new ResizeObserver(([entry]) => { if (entry.contentRect.width) setFrameSize(entry.contentRect.width) })
    observer.observe(dialog.current.querySelector('.portrait-frame'))
    return () => observer.disconnect()
  }, [])

  useEffect(() => {
    const previous = document.activeElement
    const overflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    dialog.current?.focus()
    const keydown = (event) => {
      if (event.key === 'Escape' && !busy) onClose()
      if (event.key !== 'Tab') return
      const items = [...dialog.current.querySelectorAll('button:not(:disabled), input:not(:disabled), [tabindex="0"]')]
      if (!items.length) return
      const first = items[0], last = items[items.length - 1]
      if (event.shiftKey && (document.activeElement === first || document.activeElement === dialog.current)) {
        event.preventDefault(); last.focus()
      } else if (!event.shiftKey && (document.activeElement === last || document.activeElement === dialog.current)) {
        event.preventDefault(); first.focus()
      }
    }
    document.addEventListener('keydown', keydown)
    return () => { document.body.style.overflow = overflow; previous?.focus(); document.removeEventListener('keydown', keydown) }
  }, [onClose, busy])

  useEffect(() => {
    let cancelled = false
    memorialsAPI.getMedia(memorial.id).then((res) => {
      if (!cancelled) setPhotos(res.data.filter((item) => item.media_type === 'photo'))
    }).catch(() => { if (!cancelled) setError(t('portraits.load_error')) })
    return () => { cancelled = true }
  }, [memorial.id, t])

  useEffect(() => {
    setSourceUrl(null); setDimensions(null); setError('')
    if (!selected) return
    let objectUrl
    const controller = new AbortController()
    setLoading(true)
    apiClient.get(`/media/${selected}`, { responseType: 'blob', signal: controller.signal }).then((res) => {
      objectUrl = URL.createObjectURL(res.data)
      setSourceUrl(objectUrl)
    }).catch(() => { if (!controller.signal.aborted) setError(t('portraits.load_error')) })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => { controller.abort(); if (objectUrl) URL.revokeObjectURL(objectUrl) }
  }, [selected, t])

  const width = dimensions ? (rotation % 180 ? dimensions.height : dimensions.width) : FRAME
  const height = dimensions ? (rotation % 180 ? dimensions.width : dimensions.height) : FRAME
  const base = Math.max(FRAME / width, FRAME / height)
  const scale = base * zoom
  const bounds = { x: Math.max(0, (width * scale - FRAME) / 2), y: Math.max(0, (height * scale - FRAME) / 2) }
  const position = { x: clamp(pan.x, bounds.x), y: clamp(pan.y, bounds.y) }
  const crop = {
    x: Math.max(0, ((width * scale - FRAME) / 2 - position.x) / (width * scale)),
    y: Math.max(0, ((height * scale - FRAME) / 2 - position.y) / (height * scale)),
    width: Math.min(1, FRAME / (width * scale)),
    height: Math.min(1, FRAME / (height * scale)), rotation,
  }

  const imageLoaded = (event) => {
    const d = { width: event.currentTarget.naturalWidth, height: event.currentTarget.naturalHeight }
    setDimensions(d)
    const saved = restoreCrop.current
    if (saved) {
      const w = saved.rotation % 180 ? d.height : d.width
      const h = saved.rotation % 180 ? d.width : d.height
      const restoredScale = FRAME / (saved.width * w)
      setRotation(saved.rotation)
      setZoom(restoredScale / Math.max(FRAME / w, FRAME / h))
      setPan({ x: (w * restoredScale - FRAME) / 2 - saved.x * w * restoredScale,
        y: (h * restoredScale - FRAME) / 2 - saved.y * h * restoredScale })
      restoreCrop.current = null
    }
  }

  const choose = (id) => { restoreCrop.current = null; setSelected(id); setZoom(1); setPan({ x: 0, y: 0 }); setRotation(0) }
  const upload = async (event) => {
    const file = event.target.files[0]
    event.target.value = ''
    if (!file) return
    setBusy(true); setError('')
    try {
      const res = await memorialsAPI.uploadMedia(memorial.id, file)
      setPhotos((prev) => [...prev, res.data]); choose(res.data.id)
    } catch (err) { setError(typeof err.response?.data?.detail === 'string' ? err.response.data.detail : t('media.upload_error')) }
    finally { setBusy(false) }
  }
  const save = async (follow = false) => {
    setBusy(true); setError('')
    try {
      const res = await memorialsAPI.setPortrait(memorial.id, kind, follow ? null : selected, follow ? null : crop)
      await onSaved(res.data)
    } catch (err) { setError(typeof err.response?.data?.detail === 'string' ? err.response.data.detail : t('portraits.save_error')); setBusy(false) }
  }
  const move = (x, y) => setPan({ x: clamp(position.x + x, bounds.x), y: clamp(position.y + y, bounds.y) })

  return <div className="portrait-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget && !busy) onClose() }}>
    <section className="portrait-dialog" ref={dialog} role="dialog" aria-modal="true" aria-labelledby="portrait-title" tabIndex={-1}>
      <header className="portrait-header"><div><p className="portrait-eyebrow">{t('portraits.eyebrow')}</p><h2 id="portrait-title">{t(kind === 'avatar' ? 'portraits.avatar_title' : 'portraits.cover_title')}</h2></div>
        <button type="button" onClick={onClose} disabled={busy} aria-label={t('portraits.close')}>×</button></header>
      <p className="portrait-intro">{t(kind === 'avatar' ? 'portraits.avatar_hint' : 'portraits.cover_hint')}</p>
      <div className="portrait-body">
        <div className="portrait-workspace">
          <div className={`portrait-frame ${kind === 'cover' ? 'portrait-frame--cover' : ''}`} role="group" tabIndex={0} aria-label={t('portraits.move_hint')}
            onKeyDown={(event) => { const deltas = { ArrowLeft: [-10, 0], ArrowRight: [10, 0], ArrowUp: [0, -10], ArrowDown: [0, 10] }; if (deltas[event.key]) { event.preventDefault(); move(...deltas[event.key]) } }}
            onPointerDown={(event) => { if (!dimensions || busy) return; event.currentTarget.setPointerCapture(event.pointerId); drag.current = { x: event.clientX, y: event.clientY, pan: position } }}
            onPointerMove={(event) => { if (!drag.current) return; const ratio = FRAME / event.currentTarget.clientWidth; setPan({ x: clamp(drag.current.pan.x + (event.clientX - drag.current.x) * ratio, bounds.x), y: clamp(drag.current.pan.y + (event.clientY - drag.current.y) * ratio, bounds.y) }) }}
            onPointerUp={() => { drag.current = null }} onPointerCancel={() => { drag.current = null }}>
            {sourceUrl ? <img src={sourceUrl} alt={t('portraits.preview')} draggable={false} onLoad={imageLoaded} onError={() => { setDimensions(null); setError(t('portraits.load_error')) }}
              style={{ width: dimensions ? dimensions.width * scale * frameSize / FRAME : frameSize, height: dimensions ? dimensions.height * scale * frameSize / FRAME : frameSize,
                left: `calc(50% + ${position.x * frameSize / FRAME}px)`, top: `calc(50% + ${position.y * frameSize / FRAME}px)`, transform: `translate(-50%, -50%) rotate(${rotation}deg)` }} /> : <span>{loading ? t('media.loading') : '🕯'}</span>}
            <div className="portrait-mask" aria-hidden="true" />
          </div>
          <p className="portrait-move-hint">{t('portraits.move_hint')}</p>
          <label className="portrait-zoom">{t('portraits.zoom')}<input type="range" min="1" max={Math.max(5, zoom)} step="0.01" value={zoom} disabled={!dimensions || busy} onChange={(event) => setZoom(Number(event.target.value))} /></label>
          <div className="portrait-tools"><button type="button" disabled={!dimensions || busy} onClick={() => { setRotation((value) => (value + 90) % 360); setZoom(1); setPan({ x: 0, y: 0 }) }}>{t('portraits.rotate')}</button>
            <button type="button" disabled={!dimensions || busy} onClick={() => { setRotation(0); setZoom(1); setPan({ x: 0, y: 0 }) }}>{t('portraits.reset')}</button></div>
          <p className="portrait-preserve">{t('portraits.preserve')}</p>
        </div>
        <div className="portrait-sources"><label className="portrait-upload">{busy ? t('media.uploading') : t('portraits.upload')}<input type="file" accept="image/*" disabled={busy} onChange={upload} /></label>
          <p>{t('portraits.from_album')}</p>
          {photos.length === 0 ? <p className="portrait-empty">{t('portraits.no_photos')}</p> : <div className="portrait-source-grid">{photos.map((photo) => <button key={photo.id} type="button" disabled={busy} className={selected === photo.id ? 'is-selected' : ''} aria-pressed={selected === photo.id} aria-label={t('portraits.choose_photo', { name: photo.file_name })} onClick={() => choose(photo.id)}>
            <ApiMediaImage mediaId={photo.id} thumbnail="medium" alt={photo.file_name} eager /></button>)}</div>}
        </div>
      </div>
      {error && <p className="portrait-error" role="alert">{error}</p>}
      <footer className="portrait-footer">{kind === 'avatar' && options.avatar && <button type="button" disabled={busy} onClick={() => save(true)}>{t('portraits.follow_cover')}</button>}
        <button type="button" disabled={busy} onClick={onClose}>{t('portraits.cancel')}</button><button type="button" className="portrait-save" disabled={busy || !dimensions} onClick={() => save()}>{busy ? t('portraits.saving') : t('portraits.save')}</button></footer>
    </section>
  </div>
}
