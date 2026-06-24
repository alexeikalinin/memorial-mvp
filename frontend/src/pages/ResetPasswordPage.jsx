import { useState } from 'react'
import { useSearchParams, useNavigate, Link } from 'react-router-dom'
import { authAPI } from '../api/client'
import { useLanguage } from '../contexts/LanguageContext'
import './AuthPage.css'

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')
  const navigate = useNavigate()
  const { t } = useLanguage()

  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  if (!token) {
    return (
      <div className="auth-page">
        <div className="auth-card">
          <div className="auth-logo">vspomin<span>.ai</span></div>
          <h1 className="auth-title">{t('auth.invalid_link_title')}</h1>
          <p className="auth-sub">{t('auth.invalid_link_sub')}</p>
          <Link to="/forgot-password" className="auth-btn">{t('auth.request_reset')}</Link>
        </div>
      </div>
    )
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (password !== confirm) {
      setError(t('auth.passwords_mismatch'))
      return
    }
    if (password.length < 8) {
      setError(t('auth.password_too_short'))
      return
    }
    setLoading(true)
    try {
      await authAPI.confirmPasswordReset(token, password)
      navigate('/login?reset=success')
    } catch (err) {
      setError(err.response?.data?.detail || t('auth.reset_failed'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-logo">vspomin<span>.ai</span></div>
        <h1 className="auth-title">{t('auth.set_new_password_title')}</h1>
        <p className="auth-sub">{t('auth.set_new_password_sub')}</p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="auth-field">
            <label htmlFor="password">{t('auth.new_password')}</label>
            <input
              id="password"
              type="password"
              name="new-password"
              autoComplete="new-password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder={t('auth.password_min_placeholder_short')}
              required
              minLength={8}
            />
          </div>
          <div className="auth-field">
            <label htmlFor="confirm">{t('auth.confirm_password')}</label>
            <input
              id="confirm"
              type="password"
              name="confirm-password"
              autoComplete="new-password"
              value={confirm}
              onChange={e => setConfirm(e.target.value)}
              placeholder={t('auth.repeat_password')}
              required
            />
          </div>

          {error && <p className="auth-error">{error}</p>}

          <button type="submit" className="auth-btn" disabled={loading}>
            {loading ? t('auth.saving') : t('auth.set_new_password_btn')}
          </button>
        </form>
      </div>
    </div>
  )
}
