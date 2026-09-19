import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useLanguage } from '../contexts/LanguageContext'
import './CreateMemorialTutorial.css'

const STEP_ICONS = ['🕯', '🖼', '✍️', '💬']
const TOTAL_STEPS = 4

export default function CreateMemorialTutorial({ onClose }) {
  const { t } = useLanguage()
  const [step, setStep] = useState(0)
  const navigate = useNavigate()

  const steps = t('tutorial.steps')
  const isLast = step === TOTAL_STEPS - 1
  const current = steps[step]

  const goNext = () => {
    if (isLast) {
      onClose()
      navigate('/memorials/new')
    } else {
      setStep((s) => s + 1)
    }
  }

  const goPrev = () => setStep((s) => Math.max(0, s - 1))

  const skip = () => {
    onClose()
    navigate('/memorials/new')
  }

  return (
    <div className="tutorial-overlay" onClick={onClose}>
      <div className="tutorial-card" onClick={(e) => e.stopPropagation()}>
        <button type="button" className="tutorial-close" onClick={onClose} aria-label={t('tutorial.close')}>
          ✕
        </button>

        <div className="tutorial-icon">{STEP_ICONS[step]}</div>
        <div className="tutorial-step-label">{t('tutorial.step_label', { n: step + 1, total: TOTAL_STEPS })}</div>
        <h2 className="tutorial-title">{current.title}</h2>
        <p className="tutorial-desc">{current.desc}</p>

        <div className="tutorial-dots">
          {Array.from({ length: TOTAL_STEPS }).map((_, i) => (
            <span key={i} className={`tutorial-dot${i === step ? ' tutorial-dot--active' : ''}`} />
          ))}
        </div>
        <div className="tutorial-counter">{step + 1}/{TOTAL_STEPS}</div>

        <div className="tutorial-actions">
          <button type="button" className="tutorial-skip" onClick={skip}>
            {t('tutorial.skip')}
          </button>
          <div className="tutorial-nav-buttons">
            {step > 0 && (
              <button type="button" className="btn btn-secondary tutorial-prev" onClick={goPrev}>
                {t('tutorial.back')}
              </button>
            )}
            <button type="button" className="btn btn-primary tutorial-next" onClick={goNext}>
              {isLast ? t('tutorial.finish') : t('tutorial.next')}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
