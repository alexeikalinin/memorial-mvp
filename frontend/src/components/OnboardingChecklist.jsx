import { Link } from 'react-router-dom'
import './OnboardingChecklist.css'

const STEPS = [
  {
    key: 'memorial',
    icon: '🕯',
    title: 'Create a memorial',
    desc: 'Add the person you want to remember.',
    cta: 'Create memorial',
    to: '/memorials/new',
  },
  {
    key: 'photo',
    icon: '🖼',
    title: 'Upload a photo',
    desc: 'A portrait brings the page to life.',
    cta: 'Go to memorial',
    toFn: (firstId) => `/memorials/${firstId}?tab=media`,
  },
  {
    key: 'memory',
    icon: '✍️',
    title: 'Add a memory',
    desc: 'A story, a date, a moment — anything counts.',
    cta: 'Add memory',
    toFn: (firstId) => `/memorials/${firstId}?tab=memories`,
  },
  {
    key: 'chat',
    icon: '💬',
    title: 'Chat with the avatar',
    desc: 'Ask the avatar a question and see it respond.',
    cta: 'Open chat',
    toFn: (firstId) => `/memorials/${firstId}?tab=chat`,
  },
]

export default function OnboardingChecklist({ done, firstMemorialId, onDismiss }) {
  const completedCount = Object.values(done).filter(Boolean).length
  if (completedCount === 4) return null

  return (
    <div className="ob-wrap">
      <div className="ob-header">
        <div className="ob-header-left">
          <span className="ob-title">Get started</span>
          <span className="ob-progress">{completedCount} of 4 done</span>
        </div>
        <button className="ob-dismiss" onClick={onDismiss} title="Dismiss">✕</button>
      </div>

      <div className="ob-steps">
        {STEPS.map((step) => {
          const isDone = done[step.key]
          const to = step.to ?? step.toFn?.(firstMemorialId)
          const disabled = step.key !== 'memorial' && !firstMemorialId

          return (
            <div key={step.key} className={`ob-step${isDone ? ' ob-step--done' : ''}`}>
              <div className="ob-step-icon">
                {isDone ? <span className="ob-check">✓</span> : <span>{step.icon}</span>}
              </div>
              <div className="ob-step-body">
                <span className="ob-step-title">{step.title}</span>
                {!isDone && <span className="ob-step-desc">{step.desc}</span>}
              </div>
              {!isDone && !disabled && (
                <Link to={to} className="ob-step-cta">{step.cta} →</Link>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
