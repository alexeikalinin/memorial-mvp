import { useEffect, useState } from 'react'
import apiClient from '../api/client'
import { useLanguage } from '../contexts/LanguageContext'

export default function YandexAuthButton({ from = '/', link = false }) {
  const { lang } = useLanguage()
  const en = lang === 'en'
  const [enabled, setEnabled] = useState(false)
  const [connected, setConnected] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    apiClient.get('/auth/yandex/status').then(({ data }) => {
      if (active) setEnabled(data.enabled)
    }).catch(() => {})
    if (link) apiClient.get('/auth/yandex/connection').then(({ data }) => {
      if (active) setConnected(data.connected)
    }).catch(() => {})
    return () => { active = false }
  }, [link])

  const start = async () => {
    setBusy(true)
    setError('')
    try {
      const bytes = crypto.getRandomValues(new Uint8Array(32))
      const encode = data => btoa(String.fromCharCode(...data)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
      const verifier = encode(bytes)
      const hash = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(verifier))
      sessionStorage.setItem('yandexVerifier', verifier)
      sessionStorage.setItem('authReturn', from)
      const { data } = await apiClient.post('/auth/yandex/start', {
        challenge: encode(new Uint8Array(hash)), link,
      }, { withCredentials: true })
      window.location.assign(data.url)
    } catch {
      setError(en ? 'Could not start Yandex sign-in. Please retry.' : 'Не удалось начать вход через Яндекс. Попробуйте ещё раз.')
      setBusy(false)
    }
  }

  if (!enabled) return null
  if (connected) return <span className="nav-user">{en ? 'Yandex connected' : 'Яндекс подключён'}</span>
  return (
    <>
      <button type="button" className={link ? 'nav-logout' : 'btn-google-auth'} onClick={start} disabled={busy}>
        {!link && <span aria-hidden="true" style={{ color: '#fc3f1d', fontSize: 22, fontWeight: 700 }}>Я</span>}
        {busy ? (en ? 'Opening…' : 'Открываем…') : link ? (en ? 'Connect Yandex' : 'Подключить Яндекс') : (en ? 'Sign in with Yandex ID' : 'Войти с Яндекс ID')}
      </button>
      {error && <p className="auth-error" role="alert">{error}</p>}
    </>
  )
}
