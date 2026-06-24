import { Link, useNavigate } from 'react-router-dom'
import { useLanguage } from '../contexts/LanguageContext'
import './NotFoundPage.css'

export default function NotFoundPage() {
  const navigate = useNavigate()
  const { t } = useLanguage()
  return (
    <div className="error-page">
      <div className="error-page__inner">
        <div className="error-page__code">404</div>
        <div className="error-page__candle">🕯</div>
        <h1 className="error-page__title">{t('not_found.title')}</h1>
        <p className="error-page__sub">
          {t('not_found.subtitle')}
        </p>
        <div className="error-page__actions">
          <button className="error-page__btn error-page__btn--primary" onClick={() => navigate(-1)}>
            {t('not_found.back')}
          </button>
          <Link to="/" className="error-page__btn error-page__btn--secondary">
            {t('nav.home')}
          </Link>
        </div>
      </div>
    </div>
  )
}
