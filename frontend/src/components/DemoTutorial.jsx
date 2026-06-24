import { useEffect, useRef } from 'react'
import { useLanguage } from '../contexts/LanguageContext'
import './DemoTutorial.css'

export default function DemoTutorial({ step, type, onNext, onSkip }) {
  const { t } = useLanguage()
  const steps = t('demoTutorial.steps')
  const content = steps && steps[step]
  const hintRef = useRef(null)

  // Scroll hint into view when it first appears (step 3 lands below the fold)
  useEffect(() => {
    if (type === 'hint' && hintRef.current) {
      hintRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  }, [step, type])

  if (!content) return null

  if (type === 'overlay') {
    return (
      <div className="dt-overlay" onClick={onSkip}>
        <div className="dt-card" onClick={e => e.stopPropagation()}>
          <span className="dt-emoji">{content.emoji}</span>
          <h2 className="dt-title">{content.title}</h2>
          <p className="dt-text">{content.text}</p>
          <div className="dt-actions">
            <button className="dt-btn-primary" onClick={onNext}>{content.next}</button>
            <button className="dt-btn-skip" onClick={onSkip}>{t('demoTutorial.skip')}</button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="dt-hint" ref={hintRef}>
      <span className="dt-hint-emoji">{content.emoji}</span>
      <div className="dt-hint-body">
        <strong className="dt-hint-title">{content.title}</strong>
        <span className="dt-hint-text"> {content.text}</span>
      </div>
      <button className="dt-hint-close" onClick={onNext} title={t('demoTutorial.got_it')}>✕</button>
    </div>
  )
}
