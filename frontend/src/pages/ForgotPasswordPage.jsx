import { useState } from 'react'
import { Link } from 'react-router-dom'
import { authAPI } from '../api/client'
import './AuthPage.css'

export default function ForgotPasswordPage() {
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
      setError(err.response?.data?.detail || 'Something went wrong. Please try again.')
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
          <h1 className="auth-title">Check your email</h1>
          <p className="auth-sub">
            If <strong>{email}</strong> is registered, you'll receive a password reset link shortly.
          </p>
          <p className="auth-hint">Didn't get it? Check your spam folder or try again in a few minutes.</p>
          <Link to="/login" className="auth-link">Back to login</Link>
        </div>
      </div>
    )
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-logo">vspomin<span>.ai</span></div>
        <h1 className="auth-title">Forgot password?</h1>
        <p className="auth-sub">Enter your email and we'll send you a reset link.</p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="auth-field">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              name="email"
              autoComplete="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
            />
          </div>

          {error && <p className="auth-error">{error}</p>}

          <button type="submit" className="auth-btn" disabled={loading}>
            {loading ? 'Sending…' : 'Send Reset Link'}
          </button>
        </form>

        <p className="auth-footer-link">
          <Link to="/login" className="auth-link">← Back to login</Link>
        </p>
      </div>
    </div>
  )
}
