import { Component } from 'react'
import ru from '../locales/ru'
import en from '../locales/en'
import '../pages/NotFoundPage.css'

// Class component — нет хуков, читаем язык напрямую из того же localStorage-ключа,
// что использует LanguageContext.
function currentTranslations() {
  return (typeof localStorage !== 'undefined' && localStorage.getItem('lang') === 'en') ? en : ru
}

/**
 * React Error Boundary — catches unhandled render errors anywhere in the tree.
 * Wrap the whole app (or sections) with this component.
 */
export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, info) {
    // In production, Sentry would capture this here:
    // Sentry.captureException(error, { extra: info })
    console.error('[ErrorBoundary] Unhandled error:', error, info)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (!this.state.hasError) return this.props.children

    const t = currentTranslations().errorBoundary
    const msg = this.state.error?.message || t.generic_error

    return (
      <div className="error-page">
        <div className="error-page__inner">
          <div className="error-page__candle" style={{ fontSize: '3rem' }}>⚠️</div>
          <h1 className="error-page__title">{t.title}</h1>
          <p className="error-page__sub">{msg}</p>
          <div className="error-page__actions">
            <button
              className="error-page__btn error-page__btn--primary"
              onClick={() => { this.handleReset(); window.location.href = '/' }}
            >
              {t.go_home}
            </button>
            <button
              className="error-page__btn error-page__btn--secondary"
              onClick={() => window.location.reload()}
            >
              {t.reload}
            </button>
          </div>
        </div>
      </div>
    )
  }
}
