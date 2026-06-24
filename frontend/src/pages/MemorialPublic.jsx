import { useState, useEffect } from 'react'
import { useParams, Link, useNavigate, useSearchParams } from 'react-router-dom'
import { memorialsAPI, accessAPI } from '../api/client'
import ApiMediaImage from '../components/ApiMediaImage'
import { useAuth } from '../context/AuthContext'
import { useLanguage } from '../contexts/LanguageContext'
import AvatarChat from '../components/AvatarChat'
import DemoTutorial from '../components/DemoTutorial'
import './MemorialPublic.css'

const TUTORIAL_KEY = 'demo_tutorial_v1'

const ANON_CHAT_LIMIT = 5

function MemorialPublic() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
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
  const { t, lang } = useLanguage()

  // Demo tutorial state — picks up from step 3 when coming from /demo
  const [tutorialStep, setTutorialStep] = useState(() => {
    try {
      const fromDemo = searchParams.get('demo_step')
      if (fromDemo) return parseInt(fromDemo, 10)
      const saved = localStorage.getItem(TUTORIAL_KEY)
      if (!saved || saved === 'done') return null
      const n = parseInt(saved, 10)
      return n >= 3 ? n : null
    } catch { return null }
  })

  const advanceTutorial = () => {
    const next = (tutorialStep || 0) + 1
    try { localStorage.setItem(TUTORIAL_KEY, next > 5 ? 'done' : String(next)) } catch {}
    setTutorialStep(next <= 5 ? next : null)
    // strip ?demo_step from URL without navigation
    if (searchParams.has('demo_step')) {
      searchParams.delete('demo_step')
      setSearchParams(searchParams, { replace: true })
    }
  }

  const skipTutorial = () => {
    try { localStorage.setItem(TUTORIAL_KEY, 'done') } catch {}
    setTutorialStep(null)
    if (searchParams.has('demo_step')) {
      searchParams.delete('demo_step')
      setSearchParams(searchParams, { replace: true })
    }
  }

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
        setError(err.response?.data?.detail || t('public.not_found'))
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
      alert(t('public.qr_error'))
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
      if (detail?.includes('already have access') || detail?.includes('уже есть доступ')) {
        setRequestSent(true)
      } else {
        setRequestError(detail || t('public.request_error'))
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
      setMemError(err.response?.data?.detail || t('public.memory_submit_error'))
    } finally {
      setMemSubmitting(false)
    }
  }

  if (loading) return <div className="loading">{t('public.loading')}</div>
  if (error || !memorial) return <div className="error-message">{error || t('public.not_found')}</div>

  const birthYear = memorial.birth_date ? new Date(memorial.birth_date).getFullYear() : null
  const deathYear = memorial.death_date ? new Date(memorial.death_date).getFullYear() : null

  const chatLimitReached = !user && anonCount >= ANON_CHAT_LIMIT

  return (
    <div className="memorial-public">

      {/* ── Demo banner ── */}
      {memorial.is_demo && (
        <div className="demo-banner">
          <span>📖 {t('public.demo_banner')}</span>
          <span className="demo-banner-links">
            <Link to="/demo">{t('public.demo_all_families')}</Link>
            <Link to="/register" className="demo-banner-cta">{t('public.demo_create_own')}</Link>
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
            {t('public.nav_chat')}
          </button>
          <button
            className={activeSection === 'memories' ? 'active' : ''}
            onClick={() => {
              setActiveSection('memories')
              if (tutorialStep === 3) advanceTutorial()
            }}
          >
            {t('public.nav_memories')} {memories.length > 0 && `(${memories.length})`}
          </button>
          {photos.length > 0 && (
            <button
              className={activeSection === 'photos' ? 'active' : ''}
              onClick={() => setActiveSection('photos')}
            >
              {t('public.nav_photos')} ({photos.length})
            </button>
          )}
        </nav>
      </div>

      {/* ── Content ── */}
      <div className="public-content">
        {activeSection === 'chat' && (
          <>
            {/* Anonymous chat counter hint — shown before limit is reached */}
            {!user && !showAuthPrompt && (
              <div className="anon-chat-hint">
                <span className="anon-chat-hint-dots">
                  {Array.from({ length: ANON_CHAT_LIMIT }, (_, i) => (
                    <span key={i} className={`anon-dot${i < anonCount ? ' anon-dot--used' : ''}`} />
                  ))}
                </span>
                <span className="anon-chat-hint-text">
                  {anonCount === 0
                    ? t('public.anon_hint_full', { limit: ANON_CHAT_LIMIT })
                    : t('public.anon_hint_left', { left: ANON_CHAT_LIMIT - anonCount, limit: ANON_CHAT_LIMIT })}
                  {anonCount > 0 && <Link to="/register" className="anon-hint-link">{t('public.anon_hint_link')}</Link>}
                </span>
              </div>
            )}
            {/* Limit reached: sign-up prompt */}
            {showAuthPrompt && (
              <div className="anon-limit-banner">
                <p className="anon-limit-title">{t('public.anon_limit_title', { limit: ANON_CHAT_LIMIT })}</p>
                <p className="anon-limit-sub">
                  {t('public.anon_limit_sub_1')} <strong>{t('public.anon_limit_sub_2')}</strong><br />
                  {t('public.anon_limit_sub_3')} <strong>{t('public.anon_limit_sub_4')}</strong>
                </p>
                <div className="anon-limit-actions">
                  <Link to="/register" className="btn-anon-signup">{t('public.signup_free')}</Link>
                  <Link to="/login" className="btn-anon-login">{t('public.signin')}</Link>
                </div>
              </div>
            )}
            {tutorialStep === 3 && (
              <DemoTutorial step={3} type="hint" onNext={advanceTutorial} onSkip={skipTutorial} />
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
            {(tutorialStep === 4 || tutorialStep === 5) && (
              <DemoTutorial step={tutorialStep} type="hint" onNext={advanceTutorial} onSkip={skipTutorial} />
            )}
            {memories.length === 0 ? (
              <div className="public-empty"><p>{t('public.no_memories')}</p></div>
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
                      {new Date(m.event_date).toLocaleDateString(lang === 'en' ? 'en-US' : 'ru-RU', {
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
                    <span>✓</span> {t('public.memory_thanks')}
                    <button className="btn-mem-another" onClick={() => setMemSubmitted(false)}>
                      {t('public.share_another')}
                    </button>
                  </div>
                ) : showMemoryForm ? (
                  <form className="mem-submit-form" onSubmit={handleMemSubmit}>
                    <h4 className="mem-form-title">{t('public.share_memory')}</h4>
                    <p className="mem-form-hint">{t('public.memory_review_hint')}</p>
                    <input
                      className="mem-input"
                      type="text"
                      placeholder={t('public.your_name')}
                      value={memForm.contributor_name}
                      onChange={(e) => setMemForm((f) => ({ ...f, contributor_name: e.target.value }))}
                      required
                      maxLength={100}
                    />
                    <input
                      className="mem-input"
                      type="text"
                      placeholder={t('public.title_optional')}
                      value={memForm.title}
                      onChange={(e) => setMemForm((f) => ({ ...f, title: e.target.value }))}
                      maxLength={255}
                    />
                    <textarea
                      className="mem-textarea"
                      placeholder={t('public.your_memory')}
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
                        {memSubmitting ? t('public.sending') : t('public.send_for_review')}
                      </button>
                      <button type="button" className="btn-mem-cancel" onClick={() => setShowMemoryForm(false)}>
                        {t('public.cancel')}
                      </button>
                    </div>
                  </form>
                ) : (
                  <button className="btn-share-memory" onClick={() => setShowMemoryForm(true)}>
                    + {t('public.share_memory')}
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
          ⊞ {t('public.share_qr')}
        </button>
        {showQR && (
          <div className="public-qr-panel">
            {qrLoading ? (
              <p className="qr-panel-loading">{t('public.qr_generating')}</p>
            ) : qrBlobUrl ? (
              <>
                <img src={qrBlobUrl} alt="QR Code" className="public-qr-image" />
                <p className="public-qr-hint">
                  {t('public.qr_hint_1')}<br />
                  {t('public.qr_hint_2')}
                </p>
                <div className="public-qr-url-row">
                  <code className="public-qr-url">{window.location.href}</code>
                  <button
                    className="btn-copy-small"
                    onClick={() => navigator.clipboard.writeText(window.location.href).then(() => alert(t('public.link_copied')))}
                  >
                    {t('public.copy')}
                  </button>
                </div>
                <button className="btn-download-qr" onClick={handleDownloadQR}>
                  {t('public.download_png')}
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
            <p className="request-access-sent">✓ {t('public.access_request_sent')}</p>
          ) : (
            <>
              <p className="request-access-hint">{t('public.no_access_hint')}</p>
              {requestError && <p className="request-access-error">{requestError}</p>}
              <button
                className="btn-request-access"
                onClick={handleRequestAccess}
                disabled={requestLoading}
              >
                {requestLoading ? t('public.sending') : t('public.request_access')}
              </button>
            </>
          )}
        </div>
      )}

      {/* ── Footer ── */}
      <div className="public-footer">
        <span className="public-footer-text">{t('public.memory_page')}</span>
        <Link to={`/memorials/${id}`} className="manage-link">
          {t('public.manage_memorial')}
        </Link>
      </div>
    </div>
  )
}

export default MemorialPublic
