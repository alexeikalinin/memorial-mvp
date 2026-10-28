import GoogleAuthButton from '../components/GoogleAuthButton'
import YandexAuthButton from '../components/YandexAuthButton'
import { useState, useEffect } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useLanguage } from '../contexts/LanguageContext'
import { authAPI } from '../api/client'
import './AuthPage.css'
import BrandVisual from '../components/BrandVisual'
import { safeReturn } from '../utils/authReturn'

export default function RegisterPage() {
  const { user, isLoading: authLoading, login } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const from = safeReturn(searchParams.get('next'))
  const { t } = useLanguage()

  const [form, setForm] = useState({ email: '', username: '', full_name: '', password: '' })
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!authLoading && user) {
      navigate(from, { replace: true })
    }
  }, [authLoading, user, navigate, from])

  if (!authLoading && user) {
    return null
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await authAPI.register(form)
      await login(form.email, form.password)
      navigate(from, { replace: true })
    } catch (err) {
      setError(err.response?.data?.detail || t('auth.register_error'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <BrandVisual className="auth-brand" format="square" />
        <h1 className="auth-title">{t('auth.create_account_title')}</h1>

        <GoogleAuthButton from={from} />

        <YandexAuthButton from={from} />
        <p className="auth-subtitle">{t('auth.link_provider_hint')}</p>

        <div className="auth-divider"><span>{t('auth.or_register_email')}</span></div>

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
            <label>{t('auth.username')}</label>
            <input
              type="text"
              name="username"
              value={form.username}
              onChange={e => setForm(f => ({ ...f, username: e.target.value }))}
              placeholder={t('auth.username_placeholder')}
              required
            />
            <small className="auth-hint">{t('auth.username_hint')}</small>
          </div>

          <div className="auth-field">
            <label>{t('auth.full_name')} <span style={{ opacity: 0.5, fontWeight: 400 }}>({t('auth.optional')})</span></label>
            <input
              type="text"
              name="full_name"
              value={form.full_name}
              onChange={e => setForm(f => ({ ...f, full_name: e.target.value }))}
              placeholder={t('auth.full_name_placeholder')}
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
              minLength={8}
            />
          </div>

          {error && <div className="auth-error">{error}</div>}

          <button type="submit" className="btn-auth-primary" disabled={loading}>
            {loading ? t('auth.creating_account') : t('auth.create_account_title')}
          </button>
        </form>

        <p className="auth-switch">
          {t('auth.have_account')} <Link to={`/login?next=${encodeURIComponent(from)}`}>{t('auth.signin_link')}</Link>
        </p>
      </div>
    </div>
  )
}
