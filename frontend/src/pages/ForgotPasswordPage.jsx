import { useState } from 'react'
import { Link } from 'react-router-dom'
import { authAPI } from '../api/client'
import { useLanguage } from '../contexts/LanguageContext'
import './AuthPage.css'

export default function ForgotPasswordPage() {
  const { t } = useLanguage()
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [sent, setSent] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await authAPI.requestPasswordReset(email)
      setSent(true)
    } catch (err) {
      setError(err.response?.data?.detail || t('auth.generic_error'))
    } finally {
      setLoading(false)
    }
  }

  if (sent) {
    return (
      <div className="auth-page">
        <div className="auth-card">
          <div className="auth-logo">vspomin<span>.ai</span></div>
          <div className="auth-icon auth-icon--success">✉</div>
          <h1 className="auth-title">{t('auth.check_email_title')}</h1>
          <p className="auth-sub">
            {t('auth.check_email_sub_1')} <strong>{email}</strong> {t('auth.check_email_sub_2')}
          </p>
          <p className="auth-hint">{t('auth.check_email_hint')}</p>
          <Link to="/login" className="auth-link">{t('auth.back_to_login')}</Link>
        </div>
      </div>
    )
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-logo">vspomin<span>.ai</span></div>
        <h1 className="auth-title">{t('auth.forgot_password_title')}</h1>
        <p className="auth-sub">{t('auth.forgot_password_sub')}</p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="auth-field">
            <label htmlFor="email">{t('auth.email')}</label>
            <input
              id="email"
              type="email"
              name="email"
              autoComplete="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder={t('auth.email_placeholder')}
              required
            />
          </div>

          {error && <p className="auth-error">{error}</p>}

          <button type="submit" className="auth-btn" disabled={loading}>
            {loading ? t('auth.sending') : t('auth.send_reset_link')}
          </button>
        </form>

        <p className="auth-footer-link">
          <Link to="/login" className="auth-link">{t('auth.back_to_login')}</Link>
        </p>
      </div>
    </div>
  )
}
