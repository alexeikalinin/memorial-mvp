import { useCallback, useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { useLanguage } from '../contexts/LanguageContext'
import './OnboardingTour.css'

export const ONBOARDING_STORAGE_KEY = 'vspomin_onboarding_done_v1'

export const ONBOARDING_STEPS = [
  { id: 'media_upload', tab: 'media', selector: '[data-tour="media-upload"]' },
  { id: 'memories_add', tab: 'memories', selector: '[data-tour="memories-add"]' },
  { id: 'memories_invite', tab: 'memories', selector: '[data-tour="memories-invite"]' },
  { id: 'chat_voice', tab: 'chat', selector: '[data-tour="chat-voice"]' },
  { id: 'chat_audio_toggle', tab: 'chat', selector: '[data-tour="chat-audio-toggle"]' },
]

const PAD = 8
const MAX_POLL_ATTEMPTS = 25
const POLL_INTERVAL_MS = 150

/** Анимированный тур-гайд: подсвечивает элемент интерфейса и показывает подсказку с "живым" курсором. */
function OnboardingTour({ onGoToTab, onClose }) {
  const { t } = useLanguage()
  const [stepIndex, setStepIndex] = useState(0)
  const [rect, setRect] = useState(null)
  const pollRef = useRef(null)

  const step = ONBOARDING_STEPS[stepIndex]

  const measure = useCallback(() => {
    const el = document.querySelector(step.selector)
    if (el && el.offsetParent !== null) {
      setRect(el.getBoundingClientRect())
      return true
    }
    return false
  }, [step.selector])

  useEffect(() => {
    onGoToTab(step.tab)
    setRect(null)
    let attempts = 0
    if (pollRef.current) clearInterval(pollRef.current)
    pollRef.current = setInterval(() => {
      attempts += 1
      const found = measure()
      if (found || attempts >= MAX_POLL_ATTEMPTS) {
        clearInterval(pollRef.current)
      }
    }, POLL_INTERVAL_MS)
    return () => clearInterval(pollRef.current)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stepIndex])

  useEffect(() => {
    if (!rect) return
    const el = document.querySelector(step.selector)
    if (el) el.scrollIntoView({ block: 'center', behavior: 'smooth' })
  }, [rect, step.selector])

  useEffect(() => {
    const onResize = () => measure()
    window.addEventListener('resize', onResize)
    window.addEventListener('scroll', onResize, true)
    return () => {
      window.removeEventListener('resize', onResize)
      window.removeEventListener('scroll', onResize, true)
    }
  }, [measure])

  const finish = (completed) => {
    try { localStorage.setItem(ONBOARDING_STORAGE_KEY, '1') } catch {}
    onClose(completed)
  }

  const next = () => {
    if (stepIndex >= ONBOARDING_STEPS.length - 1) {
      finish(true)
    } else {
      setStepIndex((i) => i + 1)
    }
  }

  const highlightStyle = rect
    ? {
        top: rect.top - PAD,
        left: rect.left - PAD,
        width: rect.width + PAD * 2,
        height: rect.height + PAD * 2,
      }
    : null

  const tooltipStyle = (() => {
    if (!rect) {
      return { top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }
    }
    const spaceBelow = window.innerHeight - rect.bottom
    const showBelow = spaceBelow > 220
    const top = showBelow ? rect.bottom + PAD + 14 : rect.top - PAD - 14
    const left = Math.min(Math.max(rect.left + rect.width / 2, 170), window.innerWidth - 170)
    return { top, left, transform: `translate(-50%, ${showBelow ? '0' : '-100%'})` }
  })()

  return (
    <div className="onboarding-overlay" role="dialog" aria-modal="true">
      {highlightStyle && <div className="onboarding-spotlight" style={highlightStyle} />}
      {rect && (
        <motion.div
          className="onboarding-cursor"
          animate={{ left: rect.left + rect.width / 2, top: rect.top + rect.height / 2 }}
          transition={{ type: 'spring', stiffness: 120, damping: 16 }}
        >
          <motion.span
            className="onboarding-cursor-pulse"
            animate={{ scale: [1, 0.55, 1], opacity: [0.55, 0.9, 0.55] }}
            transition={{ duration: 1.3, repeat: Infinity }}
          />
          <span className="onboarding-cursor-icon">👆</span>
        </motion.div>
      )}
      <motion.div
        key={step.id}
        className="onboarding-tooltip"
        style={tooltipStyle}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
      >
        <div className="onboarding-tooltip-step">
          {t('onboarding.step_of', { current: String(stepIndex + 1), total: String(ONBOARDING_STEPS.length) })}
        </div>
        <h4>{t(`onboarding.steps.${step.id}.title`)}</h4>
        <p>{t(`onboarding.steps.${step.id}.text`)}</p>
        <div className="onboarding-tooltip-actions">
          <button type="button" className="onboarding-skip" onClick={() => finish(false)}>
            {t('onboarding.skip')}
          </button>
          <button type="button" className="onboarding-next" onClick={next}>
            {stepIndex >= ONBOARDING_STEPS.length - 1 ? t('onboarding.finish') : t('onboarding.next')}
          </button>
        </div>
      </motion.div>
    </div>
  )
}

export default OnboardingTour
