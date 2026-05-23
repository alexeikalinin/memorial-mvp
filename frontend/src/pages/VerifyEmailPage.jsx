import { useEffect, useState } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { authAPI } from '../api/client'
import './AuthPage.css'

export default function VerifyEmailPage() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')

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
        setMessage(res.data.message || 'Email verified successfully')
      })
      .catch(err => {
        setStatus('error')
        setMessage(err.response?.data?.detail || 'Verification failed. The link may be expired.')
      })
  }, [token])

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-logo">vspomin<span>.ai</span></div>

        {status === 'loading' && (
          <>
            <h1 className="auth-title">Verifying your email…</h1>
            <p className="auth-sub">Please wait a moment.</p>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="auth-icon auth-icon--success">✓</div>
            <h1 className="auth-title">Email verified!</h1>
            <p className="auth-sub">Your account is now fully activated.</p>
            <Link to="/" className="auth-btn">Go to Dashboard →</Link>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="auth-icon auth-icon--error">✕</div>
            <h1 className="auth-title">Verification failed</h1>
            <p className="auth-sub">{message}</p>
            <p className="auth-hint">
              You can{' '}
              <Link to="/" className="auth-link">sign in</Link>
              {' '}and request a new verification email from the banner in the app.
            </p>
          </>
        )}

        {status === 'no-token' && (
          <>
            <h1 className="auth-title">Invalid link</h1>
            <p className="auth-sub">No verification token found in the URL.</p>
            <Link to="/login" className="auth-link">Back to login</Link>
          </>
        )}
      </div>
    </div>
  )
}
