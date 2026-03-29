// AUTH_HIDDEN: авторизация временно скрыта для тестирования
// Когда будет готова — убрать этот файл и раскомментировать полную версию ниже
import { Outlet } from 'react-router-dom'

export default function ProtectedRoute() {
  return <Outlet />
}

/*
// ПОЛНАЯ ВЕРСИЯ (включить когда авторизация будет активна):
import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function ProtectedRoute() {
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <div className="loading-spinner" />
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}
*/
