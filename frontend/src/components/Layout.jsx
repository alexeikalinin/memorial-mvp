import { Link, useNavigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { useLanguage, SHOW_RU_LANGUAGE_OPTION } from '../contexts/LanguageContext'
import './Layout.css'

function Layout({ children }) {
  const [scrolled, setScrolled] = useState(false)
  const { user, logout } = useAuth()
  const navigate = useNavigate()
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
          <Link to="/" className="logo">
            <span className="logo-dot" />
            <h1>{t('nav.brand')}</h1>
          </Link>
          <nav className="nav">
            {/* AUTH_HIDDEN: блок входа/выхода скрыт до включения авторизации */}
            <Link to="/">{t('nav.home')}</Link>
            <Link to="/memorials/new" className="nav-cta">{t('nav.create')}</Link>
            <div className="lang-toggle">
              {SHOW_RU_LANGUAGE_OPTION ? (
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
                <span className="lang-btn lang-btn--active" aria-current="true">EN</span>
              )}
            </div>
            {user ? (
              <div className="nav-auth">
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

