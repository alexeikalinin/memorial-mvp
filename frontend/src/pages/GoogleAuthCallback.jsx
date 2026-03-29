// Обрабатывает редирект от Google OAuth: /auth/callback?token=xxx
// Сохраняет JWT и редиректит на главную
import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { authAPI } from '../api/client'

export default function GoogleAuthCallback() {
  const navigate = useNavigate()
  const { setUserFromToken } = useAuth()

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const token = params.get('token')
    if (!token) {
      navigate('/login', { replace: true })
      return
    }
    localStorage.setItem('authToken', token)
    // Верифицировать токен и загрузить профиль
    authAPI.me()
      .then(res => {
        if (setUserFromToken) setUserFromToken(res.data)
        navigate('/', { replace: true })
      })
      .catch(() => {
        localStorage.removeItem('authToken')
        navigate('/login', { replace: true })
      })
  }, [])  // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
      <div className="loading-spinner" />
    </div>
  )
}
