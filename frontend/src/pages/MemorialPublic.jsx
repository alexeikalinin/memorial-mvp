import { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { memorialsAPI, accessAPI } from '../api/client'
import ApiMediaImage from '../components/ApiMediaImage'
import { useAuth } from '../context/AuthContext'
import AvatarChat from '../components/AvatarChat'
import './MemorialPublic.css'

function MemorialPublic() {
  const { id } = useParams()
  const [memorial, setMemorial] = useState(null)
  const [memories, setMemories] = useState([])
  const [photos, setPhotos] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeSection, setActiveSection] = useState('chat')
  const [showQR, setShowQR] = useState(false)
  const [qrBlobUrl, setQrBlobUrl] = useState(null)
  const [qrLoading, setQrLoading] = useState(false)
  const [requestSent, setRequestSent] = useState(false)
  const [requestLoading, setRequestLoading] = useState(false)
  const [requestError, setRequestError] = useState(null)
  const { user } = useAuth()

  useEffect(() => {
    const loadData = async () => {
      try {
        const [memRes, memoriesRes, mediaRes] = await Promise.all([
          memorialsAPI.get(id),
          memorialsAPI.getMemories(id),
          memorialsAPI.getMedia(id),
        ])
        setMemorial(memRes.data)
        setMemories(Array.isArray(memoriesRes.data) ? memoriesRes.data : [])
        setPhotos(Array.isArray(mediaRes.data) ? mediaRes.data.filter((m) => m.media_type === 'photo') : [])
      } catch (err) {
        setError(err.response?.data?.detail || 'Мемориал не найден')
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [id])

  const handleShowQR = async () => {
    setShowQR(true)
    if (qrBlobUrl) return
    setQrLoading(true)
    try {
      const response = await memorialsAPI.getQR(id)
      setQrBlobUrl(URL.createObjectURL(response.data))
    } catch {
      alert('Ошибка при загрузке QR-кода')
      setShowQR(false)
    } finally {
      setQrLoading(false)
    }
  }

  const handleRequestAccess = async () => {
    setRequestLoading(true)
    setRequestError(null)
    try {
      await accessAPI.requestAccess(id, { requested_role: 'viewer' })
      setRequestSent(true)
    } catch (err) {
      const detail = err.response?.data?.detail
      if (detail?.includes('already have access')) {
        setRequestSent(true)
      } else {
        setRequestError(detail || 'Ошибка при отправке запроса')
      }
    } finally {
      setRequestLoading(false)
    }
  }

  const handleDownloadQR = () => {
    if (!qrBlobUrl) return
    const a = document.createElement('a')
    a.href = qrBlobUrl
    a.download = `memorial_${id}_qr.png`
    a.click()
  }

  if (loading) return <div className="loading">Загрузка...</div>
  if (error || !memorial) return <div className="error-message">{error || 'Мемориал не найден'}</div>

  const birthYear = memorial.birth_date ? new Date(memorial.birth_date).getFullYear() : null
  const deathYear = memorial.death_date ? new Date(memorial.death_date).getFullYear() : null

  return (
    <div className="memorial-public">

      {/* ── Demo banner ── */}
      {memorial.is_demo && (
        <div className="demo-banner">
          <span>📖 This is a demo memorial.</span>
          <span className="demo-banner-links">
            <Link to="/demo">← All families</Link>
            <Link to="/register" className="demo-banner-cta">Create your own →</Link>
          </span>
        </div>
      )}

      {/* ── Hero ── */}
      <div className="public-hero">
        {memorial.cover_photo_id ? (
          <ApiMediaImage
            mediaId={memorial.cover_photo_id}
            thumbnail={null}
            alt={memorial.name}
            className="public-hero-img"
            fallback={<div className="public-hero-empty">🕯</div>}
          />
        ) : (
          <div className="public-hero-empty">🕯</div>
        )}
        <div className="public-hero-overlay" />
        <div className="public-hero-info">
          <h1 className="public-name">{memorial.name}</h1>
          {(birthYear || deathYear) && (
            <p className="public-years">
              {birthYear && <span>{birthYear}</span>}
              {birthYear && deathYear && <span className="years-dash"> — </span>}
              {deathYear && <span>{deathYear}</span>}
            </p>
          )}
        </div>
      </div>

      {/* ── Description ── */}
      {memorial.description && (
        <div className="public-description-wrap">
          <p className="public-description">{memorial.description}</p>
        </div>
      )}

      {/* ── Nav ── */}
      <div className="public-nav-wrap">
        <nav className="public-nav">
          <button
            className={activeSection === 'chat' ? 'active' : ''}
            onClick={() => setActiveSection('chat')}
          >
            Поговорить с аватаром
          </button>
          <button
            className={activeSection === 'memories' ? 'active' : ''}
            onClick={() => setActiveSection('memories')}
          >
            Воспоминания {memories.length > 0 && `(${memories.length})`}
          </button>
          {photos.length > 0 && (
            <button
              className={activeSection === 'photos' ? 'active' : ''}
              onClick={() => setActiveSection('photos')}
            >
              Фотографии ({photos.length})
            </button>
          )}
        </nav>
      </div>

      {/* ── Content ── */}
      <div className="public-content">
        {activeSection === 'chat' && (
          <AvatarChat
            memorialId={id}
            coverPhotoId={memorial.cover_photo_id}
            memorialName={memorial.name}
          />
        )}

        {activeSection === 'memories' && (
          <div className="public-memories">
            {memories.length === 0 ? (
              <div className="public-empty"><p>Воспоминания не добавлены</p></div>
            ) : (
              memories.map((m) => (
                <div key={m.id} className="public-memory-card">
                  {m.title && <h3 className="public-memory-title">{m.title}</h3>}
                  <p className="public-memory-text">{m.content}</p>
                  {m.event_date && (
                    <span className="event-date">
                      {new Date(m.event_date).toLocaleDateString('ru-RU', {
                        year: 'numeric',
                        month: 'long',
                      })}
                    </span>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {activeSection === 'photos' && (
          <div className="public-photos">
            {photos.map((p) => (
              <div key={p.id} className="public-photo-item">
                {p.file_url ? (
                  <img src={p.file_url} alt={p.file_name} />
                ) : (
                  <ApiMediaImage mediaId={p.id} thumbnail="large" alt={p.file_name} />
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ── Share / QR ── */}
      <div className="public-share-section">
        <button className="btn-share-qr" onClick={handleShowQR}>
          ⊞ Поделиться QR-кодом
        </button>
        {showQR && (
          <div className="public-qr-panel">
            {qrLoading ? (
              <p className="qr-panel-loading">Генерация QR-кода...</p>
            ) : qrBlobUrl ? (
              <>
                <img src={qrBlobUrl} alt="QR-код" className="public-qr-image" />
                <p className="public-qr-hint">
                  Отсканируйте QR-код или поделитесь ссылкой.<br />
                  Можно распечатать и разместить на памятнике.
                </p>
                <div className="public-qr-url-row">
                  <code className="public-qr-url">{window.location.href}</code>
                  <button
                    className="btn-copy-small"
                    onClick={() => navigator.clipboard.writeText(window.location.href).then(() => alert('Ссылка скопирована!'))}
                  >
                    Копировать
                  </button>
                </div>
                <button className="btn-download-qr" onClick={handleDownloadQR}>
                  Скачать PNG
                </button>
              </>
            ) : null}
          </div>
        )}
      </div>

      {/* ── Request Access (для авторизованных без доступа) ── */}
      {user && !memorial.current_user_role && !memorial.is_public && (
        <div className="public-request-access">
          {requestSent ? (
            <p className="request-access-sent">✓ Запрос отправлен — ожидайте одобрения владельца</p>
          ) : (
            <>
              <p className="request-access-hint">У вас нет доступа к управлению этим мемориалом</p>
              {requestError && <p className="request-access-error">{requestError}</p>}
              <button
                className="btn-request-access"
                onClick={handleRequestAccess}
                disabled={requestLoading}
              >
                {requestLoading ? 'Отправка...' : 'Запросить доступ'}
              </button>
            </>
          )}
        </div>
      )}

      {/* ── Footer ── */}
      <div className="public-footer">
        <span className="public-footer-text">Страница памяти</span>
        <Link to={`/memorials/${id}`} className="manage-link">
          Управление мемориалом →
        </Link>
      </div>
    </div>
  )
}

export default MemorialPublic
