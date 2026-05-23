import { Link, useNavigate } from 'react-router-dom'
import './NotFoundPage.css'

export default function NotFoundPage() {
  const navigate = useNavigate()
  return (
    <div className="error-page">
      <div className="error-page__inner">
        <div className="error-page__code">404</div>
        <div className="error-page__candle">🕯</div>
        <h1 className="error-page__title">Page not found</h1>
        <p className="error-page__sub">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <div className="error-page__actions">
          <button className="error-page__btn error-page__btn--primary" onClick={() => navigate(-1)}>
            ← Go back
          </button>
          <Link to="/" className="error-page__btn error-page__btn--secondary">
            Home
          </Link>
        </div>
      </div>
    </div>
  )
}
