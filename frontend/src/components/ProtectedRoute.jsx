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

  // Check localStorage too: login() sets the token synchronously before navigate(),
  // but React's setUser() batches and may not have flushed yet when this renders.
  const hasToken = !!localStorage.getItem('authToken')
  if (!user && !hasToken) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}
