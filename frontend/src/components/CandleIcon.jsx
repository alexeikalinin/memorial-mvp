import { useId } from 'react'

/** Compact decorative candle (hero-style) for buttons and UI flourishes */
export default function CandleIcon({ className = '' }) {
  const rid = useId().replace(/:/g, '')
  const gradId = `candleIconGrad-${rid}`
  const glowId = `candleIconGlow-${rid}`

  return (
    <svg
      className={className}
      viewBox="0 0 48 80"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden
    >
      <defs>
        <linearGradient id={gradId} x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#c8a97e" />
          <stop offset="40%" stopColor="#f0ddb8" />
          <stop offset="100%" stopColor="#a07850" />
        </linearGradient>
        <radialGradient id={glowId} cx="50%" cy="60%" r="50%">
          <stop offset="0%" stopColor="#fbbf24" stopOpacity="0.4" />
          <stop offset="100%" stopColor="#f59e0b" stopOpacity="0" />
        </radialGradient>
      </defs>
      <ellipse cx="24" cy="38" rx="20" ry="26" fill={`url(#${glowId})`} />
      <g className="candle-icon-flame">
        <path
          d="M24 10 C22 18 20 24 21 30 C22 34 23 36 24 36 C25 36 26 34 27 30 C28 24 26 18 24 10Z"
          fill="#fde68a"
        />
        <path
          d="M24 16 C23 21 22 25 23 29 C23.5 32 24 34 24 34 C24 34 24.5 32 25 29 C26 25 25 21 24 16Z"
          fill="#fbbf24"
        />
        <path d="M24 22 C23.5 25 23.5 28 24 30 C24.5 28 24.5 25 24 22Z" fill="#f97316" />
      </g>
      <rect x="16" y="34" width="16" height="36" rx="2" fill={`url(#${gradId})`} />
      <rect x="19" y="36" width="3" height="32" rx="1.5" fill="white" opacity="0.15" />
      <line x1="24" y1="34" x2="24" y2="37" stroke="#4b3a2a" strokeWidth="0.8" />
      <ellipse cx="24" cy="34" rx="7" ry="1.5" fill="#e8d5b0" />
      <rect x="12" y="70" width="24" height="4" rx="2" fill="#8b6840" />
      <rect x="10" y="73" width="28" height="3" rx="1.5" fill="#6b4f30" />
    </svg>
  )
}
