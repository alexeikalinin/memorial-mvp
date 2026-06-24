import { Link } from 'react-router-dom'
import { useLanguage } from '../contexts/LanguageContext'
import './OnboardingChecklist.css'

const STEP_DEFS = [
  { key: 'memorial', icon: '🕯', to: '/memorials/new' },
  { key: 'photo', icon: '🖼', toFn: (firstId) => `/memorials/${firstId}?tab=media` },
  { key: 'memory', icon: '✍️', toFn: (firstId) => `/memorials/${firstId}?tab=memories` },
  { key: 'chat', icon: '💬', toFn: (firstId) => `/memorials/${firstId}?tab=chat` },
]

export default function OnboardingChecklist({ done, firstMemorialId, onDismiss }) {
  const { t } = useLanguage()
  const completedCount = Object.values(done).filter(Boolean).length
  if (completedCount === 4) return null

  const copy = t('onboarding.steps')

  return (
    <div className="ob-wrap">
      <div className="ob-header">
        <div className="ob-header-left">
          <span className="ob-title">{t('onboarding.title')}</span>
          <span className="ob-progress">{t('onboarding.progress', { done: completedCount, total: 4 })}</span>
        </div>
        <button className="ob-dismiss" onClick={onDismiss} title={t('onboarding.dismiss')}>✕</button>
      </div>

      <div className="ob-steps">
        {STEP_DEFS.map((step) => {
          const isDone = done[step.key]
          const to = step.to ?? step.toFn?.(firstMemorialId)
          const disabled = step.key !== 'memorial' && !firstMemorialId
          const stepCopy = copy[step.key]

          return (
            <div key={step.key} className={`ob-step${isDone ? ' ob-step--done' : ''}`}>
              <div className="ob-step-icon">
                {isDone ? <span className="ob-check">✓</span> : <span>{step.icon}</span>}
              </div>
              <div className="ob-step-body">
                <span className="ob-step-title">{stepCopy.title}</span>
                {!isDone && <span className="ob-step-desc">{stepCopy.desc}</span>}
              </div>
              {!isDone && !disabled && (
                <Link to={to} className="ob-step-cta">{stepCopy.cta} →</Link>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
