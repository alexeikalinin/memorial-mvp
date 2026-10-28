import GoogleAuthButton from '../components/GoogleAuthButton'
import { safeReturn } from '../utils/authReturn'
import { useLanguage } from '../contexts/LanguageContext'
import './AuthPage.css'

export default function GoogleWebAuthStart() {
  const { lang } = useLanguage()
  const from = safeReturn(sessionStorage.getItem('authReturn'))
  return <div className="auth-page"><div className="auth-card">
    <h1>{lang === 'en' ? 'Google sign-in' : 'Вход через Google'}</h1>
    <GoogleAuthButton from={from} autoStart />
  </div></div>
}
