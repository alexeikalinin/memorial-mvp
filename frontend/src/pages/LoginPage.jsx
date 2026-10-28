import GoogleAuthButton from '../components/GoogleAuthButton'
import YandexAuthButton from '../components/YandexAuthButton'
import { useState, useEffect } from 'react'
import { Link, useNavigate, useLocation, useSearchParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useLanguage } from '../contexts/LanguageContext'
import './AuthPage.css'
import BrandVisual from '../components/BrandVisual'
import { safeReturn } from '../utils/authReturn'

export default function LoginPage() {
  const { user, isLoading: authLoading, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [searchParams] = useSearchParams()
  const { t } = useLanguage()
  const from = safeReturn(searchParams.get('next') || location.state?.from?.pathname)
  const resetSuccess = searchParams.get('reset') === 'success'

  const [form, setForm] = useState({ email: '', password: '' })
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!authLoading && user) {
      navigate(from, { replace: true })
    }
  }, [authLoading, user, from, navigate])

  if (!authLoading && user) {
    return null
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await login(form.email, form.password)
      navigate(from, { replace: true })
    } catch (err) {
      setError(err.response?.data?.detail || t('auth.login_error'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <BrandVisual className="auth-brand" format="square" />
        <h1 className="auth-title">{t('auth.signin_title')}</h1>
        {resetSuccess && (
          <div className="auth-success-banner">
            ✓ {t('auth.password_updated')}
          </div>
        )}

        <GoogleAuthButton from={from} />

        <YandexAuthButton from={from} />
        <p className="auth-subtitle">{t('auth.link_provider_hint')}</p>

        <div className="auth-divider"><span>{t('auth.or_signin_email')}</span></div>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="auth-field">
            <label>{t('auth.email')}</label>
            <input
              type="email"
              name="email"
              value={form.email}
              onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
              placeholder={t('auth.email_placeholder')}
              required
              autoFocus
            />
          </div>

          <div className="auth-field">
            <label>{t('auth.password')}</label>
            <input
              type="password"
              name="password"
              value={form.password}
              onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
              placeholder={t('auth.password_min_placeholder')}
              required
            />
          </div>

          {error && <div className="auth-error" role="alert">{error}</div>}

          <button type="submit" className="btn-auth-primary" disabled={loading}>
            {loading ? t('auth.signing_in') : t('auth.signin_title')}
          </button>
        </form>

        <p className="auth-switch" style={{ marginTop: '0.75rem' }}>
          <Link to="/forgot-password" style={{ fontSize: '0.875rem', color: 'var(--text-secondary, rgba(255,255,255,0.5))' }}>
            {t('auth.forgot_password')}
          </Link>
        </p>

        <p className="auth-switch">
          {t('auth.no_account')} <Link to={`/register?next=${encodeURIComponent(from)}`}>{t('auth.signup_link')}</Link>
        </p>
      </div>
    </div>
  )
}
