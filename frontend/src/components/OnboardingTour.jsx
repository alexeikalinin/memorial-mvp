import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { motion, useReducedMotion } from 'framer-motion'
import { useLanguage } from '../contexts/LanguageContext'
import { tourPointerPosition, tourTooltipPosition } from '../utils/tourLayout'
import './OnboardingTour.css'

export const ONBOARDING_STORAGE_KEY = 'vspomin_onboarding_done_v1'
export const ONBOARDING_STEPS = [
  { id: 'media_upload', tab: 'media', selector: '[data-tour="media-upload"] button' },
  { id: 'memories_tab', tab: 'media', selector: '[data-tour="tab-memories"]', nextKey: 'open_memories' },
  { id: 'memories_add', tab: 'memories', selector: '[data-tour="memories-add"]' },
  { id: 'memories_invite', tab: 'memories', selector: '[data-tour="memories-invite"]' },
  { id: 'chat_tab', tab: 'memories', selector: '[data-tour="tab-chat"]', nextKey: 'open_chat' },
  { id: 'chat_voice', tab: 'chat', selector: '[data-tour="chat-voice"] button' },
  { id: 'chat_audio_toggle', tab: 'chat', selector: '[data-tour="chat-audio-toggle"]', pointerSelector: 'input' },
]
const PAD = 8

function OnboardingTour({ onGoToTab, onClose }) {
  const { t } = useLanguage()
  const reducedMotion = useReducedMotion()
  const [stepIndex, setStepIndex] = useState(0)
  const [target, setTarget] = useState(null)
  const [ready, setReady] = useState(false)
  const [missing, setMissing] = useState(false)
  const [viewport, setViewport] = useState({ width: window.innerWidth, height: window.innerHeight })
  const [tooltipSize, setTooltipSize] = useState({ width: 340, height: 240 })
  const tooltipRef = useRef(null)
  const nextRef = useRef(null)
  const goToTabRef = useRef(onGoToTab)
  goToTabRef.current = onGoToTab
  const step = ONBOARDING_STEPS[stepIndex]

  useLayoutEffect(() => {
    const tooltip = tooltipRef.current
    if (!tooltip) return
    const update = () => setTooltipSize({ width: tooltip.offsetWidth, height: tooltip.offsetHeight })
    update()
    const observer = new ResizeObserver(update)
    observer.observe(tooltip)
    return () => observer.disconnect()
  }, [stepIndex, missing])

  useEffect(() => {
    let frame, initialFrame, poll, targetObserver, observedElement
    let stopped = false
    let scrolled = false
    const started = performance.now()
    setReady(false)
    setMissing(false)
    goToTabRef.current(step.tab)
    const measure = () => {
      if (stopped) return
      const el = document.querySelector(step.selector)
      const box = el?.getBoundingClientRect()
      if (!box || !box.width || !box.height) return false
      const rect = { top: box.top, left: box.left, right: box.right, bottom: box.bottom, width: box.width, height: box.height }
      const point = tourPointerPosition(rect, el.querySelector(step.pointerSelector || ':scope')?.getBoundingClientRect() || box)
      setTarget(previous => previous && Object.keys(rect).every(key => previous.rect[key] === rect[key]) && previous.point.x === point.x && previous.point.y === point.y ? previous : { rect, point })
      if (observedElement !== el) {
        targetObserver?.disconnect()
        observedElement = el
        targetObserver = new ResizeObserver(scheduleMeasure)
        targetObserver.observe(el)
        if (el.parentElement) targetObserver.observe(el.parentElement)
      }
      setReady(box.bottom > 0 && box.top < window.innerHeight)
      setMissing(false)
      return true
    }
    const scheduleMeasure = () => {
      cancelAnimationFrame(frame)
      frame = requestAnimationFrame(measure)
    }
    const find = () => {
      if (stopped) return
      const el = document.querySelector(step.selector)
      if (el?.getBoundingClientRect().width) {
        if (!scrolled) {
          scrolled = true
          // One scroll per step. Scroll events update the target throughout the movement.
          el.scrollIntoView({ block: 'center', inline: 'nearest', behavior: reducedMotion ? 'instant' : 'smooth' })
        }
        measure()
      } else if (performance.now() - started < 5000) {
        poll = setTimeout(find, 100)
      } else {
        setMissing(true)
      }
    }
    const resize = () => {
      setViewport({ width: window.innerWidth, height: window.innerHeight })
      scheduleMeasure()
    }
    // Async data can replace the Clone button with Change without scrolling.
    const domObserver = new MutationObserver(scheduleMeasure)
    domObserver.observe(document.body, { childList: true, subtree: true })
    document.fonts?.ready.then(() => { if (!stopped) scheduleMeasure() })
    window.addEventListener('scroll', scheduleMeasure, true)
    window.addEventListener('resize', resize)
    // DOM updates must not cancel the initial target lookup and scroll.
    initialFrame = requestAnimationFrame(find)
    return () => {
      stopped = true
      cancelAnimationFrame(initialFrame)
      cancelAnimationFrame(frame)
      clearTimeout(poll)
      targetObserver?.disconnect()
      domObserver.disconnect()
      window.removeEventListener('scroll', scheduleMeasure, true)
      window.removeEventListener('resize', resize)
    }
  }, [step, reducedMotion])

  useEffect(() => {
    const previousFocus = document.activeElement
    nextRef.current?.focus({ preventScroll: true })
    return () => { if (previousFocus?.isConnected) previousFocus.focus({ preventScroll: true }) }
  }, [])

  useEffect(() => {
    if ((ready || missing) && !tooltipRef.current?.contains(document.activeElement)) nextRef.current?.focus({ preventScroll: true })
  }, [ready, missing])

  const finish = completed => {
    try { localStorage.setItem(ONBOARDING_STORAGE_KEY, '1') } catch { /* Storage may be unavailable. */ }
    onClose(completed)
  }
  const next = () => stepIndex === ONBOARDING_STEPS.length - 1 ? finish(true) : setStepIndex(i => i + 1)
  const rect = ready ? target?.rect : null
  const position = tourTooltipPosition(missing ? null : target?.rect, viewport, tooltipSize)
  const transition = reducedMotion ? { duration: 0 } : { duration: .42, ease: [.22, 1, .36, 1] }
  const onKeyDown = e => {
    if (e.key === 'Escape') { e.preventDefault(); finish(false) }
    if (e.key === 'Tab') {
      const buttons = [...tooltipRef.current.querySelectorAll('button:not(:disabled)')]
      const first = buttons[0], last = buttons[buttons.length - 1]
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus() }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus() }
    }
  }

  return createPortal(
    <div className={`onboarding-overlay${rect ? '' : ' onboarding-overlay--waiting'}`} role="dialog" aria-modal="true" aria-labelledby="onboarding-title" onKeyDown={onKeyDown}>
      {target && <motion.div className="onboarding-spotlight" initial={false} animate={{ top: target.rect.top - PAD, left: target.rect.left - PAD, width: target.rect.width + PAD * 2, height: target.rect.height + PAD * 2, opacity: ready ? 1 : 0 }} transition={transition} />}
      {target && <motion.div className="onboarding-cursor" aria-hidden="true" initial={false} animate={{ x: target.point.x, y: target.point.y, opacity: ready ? 1 : 0 }} transition={transition}>
        <span className="onboarding-cursor-pulse" />
        <svg width="26" height="32" viewBox="0 0 26 32" fill="none"><path d="M3 2v24l6-6 5 10 5-3-5-9h9L3 2Z" fill="#fbf8f1" stroke="#8e603e" strokeWidth="1.7" strokeLinejoin="round" /></svg>
      </motion.div>}
      <motion.div ref={tooltipRef} className={`onboarding-tooltip${step.nextKey ? ' onboarding-tooltip--navigation' : ''}`} initial={false} animate={position} transition={transition}>
        <div className="onboarding-tooltip-step">{t('onboarding.step_of', { current: String(stepIndex + 1), total: String(ONBOARDING_STEPS.length) })}</div>
        <div className="onboarding-progress" aria-hidden="true">{ONBOARDING_STEPS.map((item, index) => <span key={item.id} className={index <= stepIndex ? 'active' : ''} />)}</div>
        <div aria-live="polite" aria-atomic="true">
          <h4 id="onboarding-title">{t(`onboarding.steps.${step.id}.title`)}</h4>
          <p>{t(`onboarding.steps.${step.id}.text`)}</p>
          {missing && <p className="onboarding-unavailable">{t('onboarding.unavailable')}</p>}
        </div>
        <div className="onboarding-tooltip-actions">
          <button type="button" className="onboarding-skip" onClick={() => finish(false)}>{t('onboarding.skip')}</button>
          <div className="onboarding-nav">
            {stepIndex > 0 && <button type="button" className="onboarding-back" onClick={() => setStepIndex(i => i - 1)}>{t('onboarding.back')}</button>}
            <button ref={nextRef} type="button" className="onboarding-next" onClick={next} disabled={!ready && !missing}>{stepIndex === ONBOARDING_STEPS.length - 1 ? t('onboarding.finish') : t(`onboarding.${step.nextKey || 'next'}`)}</button>
          </div>
        </div>
      </motion.div>
    </div>, document.body
  )
}
export default OnboardingTour
