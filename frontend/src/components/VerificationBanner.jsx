import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { useLanguage } from '../contexts/LanguageContext'
import { authAPI } from '../api/client'
import './VerificationBanner.css'

/**
 * Soft email verification banner.
 * Shown to authenticated users whose email is not yet verified.
 * Non-blocking — just a reminder with a "Resend" button.
 */
export default function VerificationBanner() {
  const { user } = useAuth()
  const { t } = useLanguage()
  const [dismissed, setDismissed] = useState(false)
  const [sending, setSending] = useState(false)
  const [sent, setSent] = useState(false)

  // Only show to logged-in, non-demo users with unverified email
  if (!user || user.email_verified || user.is_demo || dismissed) return null

  const handleResend = async () => {
    setSending(true)
    try {
      await authAPI.resendVerification()
      setSent(true)
    } catch (e) {
      // ignore — already logged by interceptor
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="verify-banner" role="alert">
      <span className="verify-banner__icon">✉</span>
      <span className="verify-banner__text">
        {sent
          ? t('verifyBanner.sent')
          : <>{t('verifyBanner.prompt_1')} (<strong>{user.email}</strong>) {t('verifyBanner.prompt_2')}</>
        }
      </span>
      {!sent && (
        <button
          className="verify-banner__btn"
          onClick={handleResend}
          disabled={sending}
        >
          {sending ? t('verifyBanner.sending') : t('verifyBanner.resend')}
        </button>
      )}
      <button
        className="verify-banner__close"
        onClick={() => setDismissed(true)}
        aria-label={t('verifyBanner.dismiss')}
      >
        ✕
      </button>
    </div>
  )
}
