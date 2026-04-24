import { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { memorialsAPI, accessAPI } from '../api/client'
import ApiMediaImage from '../components/ApiMediaImage'
import { useAuth } from '../context/AuthContext'
import AvatarChat from '../components/AvatarChat'
import './MemorialPublic.css'

const ANON_CHAT_LIMIT = 5

function MemorialPublic() {
  const { id } = useParams()
  const navigate = useNavigate()
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

  // Anonymous chat limit
  const anonKey = `anon_chat_${id}`
  const [anonCount, setAnonCount] = useState(() => {
    try { return parseInt(localStorage.getItem(anonKey) || '0', 10) } catch { return 0 }
  })
  const [showAuthPrompt, setShowAuthPrompt] = useState(false)

  // Memory submission form
  const [showMemoryForm, setShowMemoryForm] = useState(false)
  const [memForm, setMemForm] = useState({ contributor_name: '', title: '', content: '' })
  const [memSubmitting, setMemSubmitting] = useState(false)
  const [memSubmitted, setMemSubmitted] = useState(false)
  const [memError, setMemError] = useState(null)

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
        setError(err.response?.data?.detail || 'Memorial not found')
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [id])

  // Called by AvatarChat each time user sends a message (anonymous only)
  const handleAnonChatMessage = () => {
    if (user) return
    const next = anonCount + 1
    setAnonCount(next)
    try { localStorage.setItem(anonKey, String(next)) } catch {}
    if (next >= ANON_CHAT_LIMIT) setShowAuthPrompt(true)
  }

  const handleShowQR = async () => {
    setShowQR(true)
    if (qrBlobUrl) return
    setQrLoading(true)
    try {
      const response = await memorialsAPI.getQR(id)
      setQrBlobUrl(URL.createObjectURL(response.data))
    } catch {
      alert('Error generating QR code')
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
        setRequestError(detail || 'Error sending request')
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

  const handleMemSubmit = async (e) => {
    e.preventDefault()
    setMemSubmitting(true)
    setMemError(null)
    try {
      await memorialsAPI.submitPublicMemory(id, memForm)
      setMemSubmitted(true)
      setMemForm({ contributor_name: '', title: '', content: '' })
    } catch (err) {
      setMemError(err.response?.data?.detail || 'Failed to submit memory')
    } finally {
      setMemSubmitting(false)
    }
  }

  if (loading) return <div className="loading">Loading...</div>
  if (error || !memorial) return <div className="error-message">{error || 'Memorial not found'}</div>

  const birthYear = memorial.birth_date ? new Date(memorial.birth_date).getFullYear() : null
  const deathYear = memorial.death_date ? new Date(memorial.death_date).getFullYear() : null

  const chatLimitReached = !user && anonCount >= ANON_CHAT_LIMIT

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
            Chat with Avatar
          </button>
          <button
            className={activeSection === 'memories' ? 'active' : ''}
            onClick={() => setActiveSection('memories')}
          >
            Memories {memories.length > 0 && `(${memories.length})`}
          </button>
          {photos.length > 0 && (
            <button
              className={activeSection === 'photos' ? 'active' : ''}
              onClick={() => setActiveSection('photos')}
            >
              Photos ({photos.length})
            </button>
          )}
        </nav>
      </div>

      {/* ── Content ── */}
      <div className="public-content">
        {activeSection === 'chat' && (
          <>
            {/* Anonymous chat limit prompt */}
            {showAuthPrompt && (
              <div className="anon-limit-banner">
                <p className="anon-limit-title">You've asked {ANON_CHAT_LIMIT} questions</p>
                <p className="anon-limit-sub">Create a free account to keep chatting and save your conversation.</p>
                <div className="anon-limit-actions">
                  <Link to="/register" className="btn-anon-signup">Sign up — it's free</Link>
                  <Link to="/login" className="btn-anon-login">Sign in</Link>
                </div>
              </div>
            )}
            {!chatLimitReached && (
              <AvatarChat
                memorialId={id}
                coverPhotoId={memorial.cover_photo_id}
                memorialName={memorial.name}
                onMessageSent={handleAnonChatMessage}
              />
            )}
          </>
        )}

        {activeSection === 'memories' && (
          <div className="public-memories">
            {memories.length === 0 ? (
              <div className="public-empty"><p>No memories have been shared yet.</p></div>
            ) : (
              memories.map((m) => (
                <div key={m.id} className="public-memory-card">
                  {m.title && <h3 className="public-memory-title">{m.title}</h3>}
                  <p className="public-memory-text">{m.content}</p>
                  {m.contributor_name && (
                    <span className="memory-contributor">— {m.contributor_name}</span>
                  )}
                  {m.event_date && (
                    <span className="event-date">
                      {new Date(m.event_date).toLocaleDateString('en-US', {
                        year: 'numeric',
                        month: 'long',
                      })}
                    </span>
                  )}
                </div>
              ))
            )}

            {/* Share a memory section */}
            {memorial.is_public && (
              <div className="public-submit-memory">
                {memSubmitted ? (
                  <div className="mem-submitted-msg">
                    <span>✓</span> Thank you! Your memory has been sent to the owner for review.
                    <button className="btn-mem-another" onClick={() => setMemSubmitted(false)}>
                      Share another
                    </button>
                  </div>
                ) : showMemoryForm ? (
                  <form className="mem-submit-form" onSubmit={handleMemSubmit}>
                    <h4 className="mem-form-title">Share a memory</h4>
                    <p className="mem-form-hint">Your submission will be reviewed by the memorial owner before appearing here.</p>
                    <input
                      className="mem-input"
                      type="text"
                      placeholder="Your name *"
                      value={memForm.contributor_name}
                      onChange={(e) => setMemForm((f) => ({ ...f, contributor_name: e.target.value }))}
                      required
                      maxLength={100}
                    />
                    <input
                      className="mem-input"
                      type="text"
                      placeholder="Title (optional)"
                      value={memForm.title}
                      onChange={(e) => setMemForm((f) => ({ ...f, title: e.target.value }))}
                      maxLength={255}
                    />
                    <textarea
                      className="mem-textarea"
                      placeholder="Your memory *"
                      value={memForm.content}
                      onChange={(e) => setMemForm((f) => ({ ...f, content: e.target.value }))}
                      required
                      minLength={10}
                      maxLength={5000}
                      rows={5}
                    />
                    {memError && <p className="mem-error">{memError}</p>}
                    <div className="mem-form-actions">
                      <button type="submit" className="btn-mem-submit" disabled={memSubmitting}>
                        {memSubmitting ? 'Sending…' : 'Send for review'}
                      </button>
                      <button type="button" className="btn-mem-cancel" onClick={() => setShowMemoryForm(false)}>
                        Cancel
                      </button>
                    </div>
                  </form>
                ) : (
                  <button className="btn-share-memory" onClick={() => setShowMemoryForm(true)}>
                    + Share a memory
                  </button>
                )}
              </div>
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
          ⊞ Share QR Code
        </button>
        {showQR && (
          <div className="public-qr-panel">
            {qrLoading ? (
              <p className="qr-panel-loading">Generating QR code...</p>
            ) : qrBlobUrl ? (
              <>
                <img src={qrBlobUrl} alt="QR Code" className="public-qr-image" />
                <p className="public-qr-hint">
                  Scan the QR code or share the link.<br />
                  Print and place on the memorial stone.
                </p>
                <div className="public-qr-url-row">
                  <code className="public-qr-url">{window.location.href}</code>
                  <button
                    className="btn-copy-small"
                    onClick={() => navigator.clipboard.writeText(window.location.href).then(() => alert('Link copied!'))}
                  >
                    Copy
                  </button>
                </div>
                <button className="btn-download-qr" onClick={handleDownloadQR}>
                  Download PNG
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
            <p className="request-access-sent">✓ Access request sent — waiting for owner approval</p>
          ) : (
            <>
              <p className="request-access-hint">You don't have management access to this memorial</p>
              {requestError && <p className="request-access-error">{requestError}</p>}
              <button
                className="btn-request-access"
                onClick={handleRequestAccess}
                disabled={requestLoading}
              >
                {requestLoading ? 'Sending...' : 'Request access'}
              </button>
            </>
          )}
        </div>
      )}

      {/* ── Footer ── */}
      <div className="public-footer">
        <span className="public-footer-text">Memory page</span>
        <Link to={`/memorials/${id}`} className="manage-link">
          Manage memorial →
        </Link>
      </div>
    </div>
  )
}

export default MemorialPublic
