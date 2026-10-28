import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import apiClient, { authAPI } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { useLanguage } from '../contexts/LanguageContext'
import { safeReturn } from '../utils/authReturn'
import './AuthPage.css'

const yandexMessages = {
  existing_account: ['Аккаунт с этой почтой уже есть. Войдите через Google или пароль, затем нажмите «Подключить Яндекс» в верхнем меню.', 'An account with this email already exists. Sign in with Google or your password, then select Connect Yandex in the top menu.'],
  linked_elsewhere: ['Этот Яндекс уже связан с другим аккаунтом, либо к вашему аккаунту подключён другой Яндекс.', 'This Yandex account is linked elsewhere, or you already connected another Yandex account.'],
  cancelled: ['Вход через Яндекс отменён.', 'Yandex sign-in was cancelled.'],
  profile: ['Яндекс не передал необходимые данные. Разрешите доступ к почте и основным данным профиля.', 'Yandex did not provide the required profile. Allow access to email and basic profile data.'],
  expired: ['Попытка входа истекла. Начните вход заново в этой вкладке.', 'Sign-in expired. Start again in this tab.'],
}

export default function OAuthCallback({ provider }) {
  const navigate = useNavigate()
  const { setUserFromToken, user } = useAuth()
  const { lang } = useLanguage()
  const google = provider === 'google'
  const name = google ? 'Google' : (lang === 'en' ? 'Yandex' : 'Яндекс')
  const messages = google ? {
    ...yandexMessages,
    existing_account: ['Аккаунт с этой почтой уже есть. Войдите через Яндекс или пароль, затем нажмите «Подключить Google» в верхнем меню.', 'An account with this email already exists. Sign in with Yandex or your password, then select Connect Google in the top menu.'],
    linked_elsewhere: ['Этот Google уже связан с другим аккаунтом, либо к вашему аккаунту подключён другой Google.', 'This Google account is linked elsewhere, or you already connected another Google account.'],
    cancelled: ['Вход через Google отменён.', 'Google sign-in was cancelled.'],
    profile: ['Google не подтвердил необходимые данные. Используйте профиль с подтверждённой почтой.', 'Google did not verify the required profile. Use a verified email address.'],
  } : yandexMessages
  const [result] = useState(() => new URLSearchParams(window.location.hash.slice(1)))
  const [error, setError] = useState(result.get(`${provider}_error`) || '')
  const pending = useRef(null)

  useEffect(() => {
    window.history.replaceState(null, '', window.location.pathname)
    const code = result.get(`${provider}_code`)
    if (!code || result.get(`${provider}_error`)) {
      setError(result.get(`${provider}_error`) || 'expired')
      return
    }
    let active = true
    if (!pending.current) {
      pending.current = (async () => {
        const verifier = sessionStorage.getItem(`${provider}Verifier`)
        if (!verifier) throw new Error('expired')
        const { data } = await apiClient.post(`/auth/${provider}/exchange`, { code, verifier })
        sessionStorage.removeItem(`${provider}Verifier`)
        localStorage.setItem('authToken', data.access_token)
        try {
          const profile = await authAPI.me()
          return { profile: profile.data, isNew: data.new_user }
        } catch (err) {
          localStorage.removeItem('authToken')
          throw err
        }
      })()
    }
    pending.current.then(({ profile, isNew }) => {
      if (!active) return
      setUserFromToken(profile)
      const target = safeReturn(sessionStorage.getItem('authReturn'), isNew ? '/?tutorial=1' : '/')
      sessionStorage.removeItem('authReturn')
      navigate(target, { replace: true })
    }).catch(() => { if (active) setError('expired') })
    return () => { active = false }
  }, [navigate, result, setUserFromToken, provider])

  if (!error) return <div className="auth-page" role="status">{lang === 'en' ? 'Signing in…' : 'Входим…'}</div>
  const text = messages[error] || [`Не удалось войти через ${name}. Попробуйте ещё раз.`, `${name} sign-in failed. Please retry.`]
  return (
    <div className="auth-page"><div className="auth-card">
      <h1 className="auth-title">{lang === 'en' ? `${name} sign-in` : `Вход через ${name}`}</h1>
      <p role="alert">{text[lang === 'en' ? 1 : 0]}</p>
      <Link to={user ? '/' : '/login'}>{lang === 'en' ? 'Continue' : 'Продолжить'}</Link>
    </div></div>
  )
}
