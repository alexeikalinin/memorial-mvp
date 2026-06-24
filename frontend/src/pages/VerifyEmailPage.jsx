import { useEffect, useState } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { authAPI } from '../api/client'
import { useLanguage } from '../contexts/LanguageContext'
import './AuthPage.css'

export default function VerifyEmailPage() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')
  const { t } = useLanguage()

  const [status, setStatus] = useState('loading') // 'loading' | 'success' | 'error' | 'no-token'
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (!token) {
      setStatus('no-token')
      return
    }
    authAPI.verifyEmail(token)
      .then(res => {
        setStatus('success')
        setMessage(res.data.message || t('verifyEmail.default_success'))
      })
      .catch(err => {
        setStatus('error')
        setMessage(err.response?.data?.detail || t('verifyEmail.default_error'))
      })
  }, [token])

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-logo">vspomin<span>.ai</span></div>

        {status === 'loading' && (
          <>
            <h1 className="auth-title">{t('verifyEmail.loading_title')}</h1>
            <p className="auth-sub">{t('verifyEmail.loading_sub')}</p>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="auth-icon auth-icon--success">✓</div>
            <h1 className="auth-title">{t('verifyEmail.success_title')}</h1>
            <p className="auth-sub">{t('verifyEmail.success_sub')}</p>
            <Link to="/" className="auth-btn">{t('verifyEmail.go_dashboard')}</Link>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="auth-icon auth-icon--error">✕</div>
            <h1 className="auth-title">{t('verifyEmail.error_title')}</h1>
            <p className="auth-sub">{message}</p>
            <p className="auth-hint">
              {t('verifyEmail.error_hint_1')}{' '}
              <Link to="/" className="auth-link">{t('verifyEmail.error_hint_link')}</Link>
              {' '}{t('verifyEmail.error_hint_2')}
            </p>
          </>
        )}

        {status === 'no-token' && (
          <>
            <h1 className="auth-title">{t('verifyEmail.no_token_title')}</h1>
            <p className="auth-sub">{t('verifyEmail.no_token_sub')}</p>
            <Link to="/login" className="auth-link">{t('auth.back_to_login')}</Link>
          </>
        )}
      </div>
    </div>
  )
}
