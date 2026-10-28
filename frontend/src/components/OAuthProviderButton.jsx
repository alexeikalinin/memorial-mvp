import { useEffect, useState, useCallback, useRef } from 'react'
import apiClient from '../api/client'
import { useAuth } from '../context/AuthContext'
import { useLanguage } from '../contexts/LanguageContext'

export default function OAuthProviderButton({ provider, from = '/', link = false, autoStart = false }) {
  const { lang } = useLanguage()
  const en = lang === 'en'
  const name = provider === 'google' ? 'Google' : (en ? 'Yandex' : 'Яндекс')
  const { user } = useAuth()
  const autoStarted = useRef(false)
  const [enabled, setEnabled] = useState(false)
  const [connected, setConnected] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    setEnabled(false)
    setConnected(false)
    apiClient.get(`/auth/${provider}/status`).then(({ data }) => {
      if (active) setEnabled(data.enabled)
    }).catch(() => {})
    if (link) apiClient.get(`/auth/${provider}/connection`).then(({ data }) => {
      if (active) setConnected(data.connected)
    }).catch(() => {})
    return () => { active = false }
  }, [link, provider, user?.id])

  const start = useCallback(async () => {
    setBusy(true)
    setError('')
    try {
      const bytes = crypto.getRandomValues(new Uint8Array(32))
      const encode = data => btoa(String.fromCharCode(...data)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
      const verifier = encode(bytes)
      const hash = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(verifier))
      sessionStorage.setItem(`${provider}Verifier`, verifier)
      sessionStorage.setItem('authReturn', from)
      const { data } = await apiClient.post(`/auth/${provider}/start`, {
        challenge: encode(new Uint8Array(hash)), link,
      }, { withCredentials: true })
      window.location.assign(data.url)
    } catch {
      setError(en ? `Could not start ${provider === 'google' ? 'Google' : 'Yandex'} sign-in. Please retry.` : `Не удалось начать вход через ${provider === 'google' ? 'Google' : 'Яндекс'}. Попробуйте ещё раз.`)
      setBusy(false)
    }
  }, [from, link, provider, en])

  useEffect(() => {
    if (enabled && autoStart && !autoStarted.current) {
      autoStarted.current = true
      start()
    }
  }, [enabled, autoStart, start])

  if (!enabled) return null
  if (connected) return <span className="nav-user">{en ? `${name} connected` : `${name} подключён`}</span>
  return (
    <>
      <button type="button" className={link ? 'nav-logout' : 'btn-google-auth'} onClick={start} disabled={busy}>
        {!link && <span aria-hidden="true" style={{ color: provider === 'google' ? '#4285f4' : '#fc3f1d', fontSize: 22, fontWeight: 700 }}>{provider === 'google' ? 'G' : 'Я'}</span>}
        {busy ? (en ? 'Opening…' : 'Открываем…') : link ? (en ? `Connect ${name}` : `Подключить ${name}`) : (en ? `Sign in with ${name}` : `Войти с ${name}${provider === 'yandex' ? ' ID' : ''}`)}
      </button>
      {error && <p className="auth-error" role="alert">{error}</p>}
    </>
  )
}
