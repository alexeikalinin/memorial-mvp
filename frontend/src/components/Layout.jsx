import YandexAuthButton from './YandexAuthButton'
import apiClient from '../api/client'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { useLanguage, SHOW_EN_LANGUAGE_OPTION } from '../contexts/LanguageContext'
import VerificationBanner from './VerificationBanner'
import BrandVisual from './BrandVisual'
import './Layout.css'

function Layout({ children }) {
  const [exportBusy, setExportBusy] = useState(false)
  const [exportError, setExportError] = useState('')
  const downloadArchive = async () => {
    setExportBusy(true); setExportError('')
    try {
      const manifest = await apiClient.get('/account/export/manifest')
      const chats = {}
      for (const id of manifest.data.memorial_ids || []) {
        try {
          const history = JSON.parse(localStorage.getItem(`chat_${id}`) || '[]')
          if (Array.isArray(history)) chats[String(id)] = history
        } catch { /* Corrupt local history does not prevent the server archive. */ }
      }
      const { data } = await apiClient.post('/account/export', { chats }, { responseType: 'blob', timeout: 0 })
      const url = URL.createObjectURL(data)
      const link = document.createElement('a'); link.href = url; link.download = 'vspomin-archive.zip'; link.click()
      setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch { setExportError(lang === 'en' ? 'Could not export the full archive. Please retry.' : 'Не удалось выгрузить полный архив. Попробуйте ещё раз.') }
    finally { setExportBusy(false) }
  }
  const [scrolled, setScrolled] = useState(false)
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const { lang, setLang, t } = useLanguage()

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 8)
    window.addEventListener('scroll', handler, { passive: true })
    return () => window.removeEventListener('scroll', handler)
  }, [])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="layout">
      <header className={`header${scrolled ? ' scrolled' : ''}`}>
        <div className="container">
          <Link to="/" className="logo" aria-label="vspomin.ai">
            <BrandVisual className="header-brand" tone="light" />
          </Link>
          <nav className="nav">
            {/* AUTH_HIDDEN: блок входа/выхода скрыт до включения авторизации */}
            <Link to="/">{t('nav.home')}</Link>
            <Link to="/memorials/new" className="nav-cta">{t('nav.create')}</Link>
            <div className="lang-toggle">
              {SHOW_EN_LANGUAGE_OPTION ? (
                <>
                  <button
                    type="button"
                    className={`lang-btn${lang === 'ru' ? ' lang-btn--active' : ''}`}
                    onClick={() => setLang('ru')}
                  >RU</button>
                  <span className="lang-sep">|</span>
                  <button
                    type="button"
                    className={`lang-btn${lang === 'en' ? ' lang-btn--active' : ''}`}
                    onClick={() => setLang('en')}
                  >EN</button>
                </>
              ) : (
                <span className="lang-btn lang-btn--active" aria-current="true">RU</span>
              )}
            </div>
            {user ? (
              <div className="nav-auth">
                <YandexAuthButton link from={location.pathname + location.search} />
                <button type="button" className="nav-logout" disabled={exportBusy} onClick={downloadArchive}>{exportBusy ? (lang === 'en' ? 'Preparing archive…' : 'Подготовка архива…') : (lang === 'en' ? 'Download archive' : 'Скачать архив')}</button>
                <span className="nav-user" title={user.email || user.username}>
                  {user.email || user.username}
                </span>
                <button type="button" className="nav-logout" data-testid="logout-btn" onClick={handleLogout}>
                  {t('nav.logout')}
                </button>
              </div>
            ) : null}
          </nav>
        </div>
      </header>
      <VerificationBanner />
      {exportError && <p role="alert">{exportError}</p>}
      <main className="main">
        {children}
      </main>
      <footer className="footer">
        <div className="container">
          <p>{t('nav.footer')}</p>
          <span className="footer-flame">🕯</span>
        </div>
      </footer>
    </div>
  )
}

export default Layout
