import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { LanguageProvider } from './contexts/LanguageContext'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import ErrorBoundary from './components/ErrorBoundary'
import { AuthProvider } from './context/AuthContext'
import Home from './pages/Home'
import MemorialCreate from './pages/MemorialCreate'
import MemorialDetail from './pages/MemorialDetail'
import MemorialPublic from './pages/MemorialPublic'
import ContributePage from './pages/ContributePage'
import DemoPage from './pages/DemoPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import GoogleAuthCallback from './pages/GoogleAuthCallback'
import ForgotPasswordPage from './pages/ForgotPasswordPage'
import ResetPasswordPage from './pages/ResetPasswordPage'
import VerifyEmailPage from './pages/VerifyEmailPage'
import NotFoundPage from './pages/NotFoundPage'

function App() {
  const base =
    import.meta.env.BASE_URL === '/' ? undefined : import.meta.env.BASE_URL.replace(/\/$/, '')
  return (
    <ErrorBoundary>
    <LanguageProvider>
    <AuthProvider>
      <Router
        basename={base}
        future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true,
        }}
      >
        <Layout>
          <Routes>
            {/* Публичные маршруты */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/auth/callback" element={<GoogleAuthCallback />} />
            <Route path="/verify-email" element={<VerifyEmailPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />
            <Route path="/m/:id" element={<MemorialPublic />} />
            <Route path="/demo" element={<DemoPage />} />
            <Route path="/contribute/:token" element={<ContributePage />} />

            {/* Защищённые маршруты */}
            <Route element={<ProtectedRoute />}>
              <Route path="/" element={<Home />} />
              <Route path="/memorials/new" element={<MemorialCreate />} />
              <Route path="/memorials/:id" element={<MemorialDetail />} />
            </Route>

            {/* 404 — must be last */}
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </Layout>
      </Router>
    </AuthProvider>
    </LanguageProvider>
    </ErrorBoundary>
  )
}

export default App

