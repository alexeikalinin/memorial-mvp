import './DemoTutorial.css'

const STEPS = {
  1: {
    emoji: '👨‍👩‍👧‍👦',
    title: '4 families. 5 generations.',
    text: 'Each family has its own memorials, memories, and AI avatars built from real stories. Click any family to explore.',
    next: "Let's go →",
  },
  2: {
    emoji: '🕯',
    title: 'Meet the family',
    text: 'Each person here has their own memories and an AI avatar. Click anyone to start a conversation.',
    next: 'Got it →',
  },
  3: {
    emoji: '💬',
    title: 'Chat with the avatar',
    text: 'Ask anything — the avatar responds based on real memories. The more memories are added, the richer the conversation becomes.',
    next: 'Got it',
  },
  4: {
    emoji: '📖',
    title: 'Memories power the avatar',
    text: 'Everything the avatar knows comes from these memories. Anyone you share the link with can contribute more.',
    next: 'Got it',
  },
  5: {
    emoji: '🌳',
    title: 'One big family',
    text: 'All these people are connected across generations. Avatars can reference shared memories — ask Sean about his great-grandchildren.',
    next: 'Got it',
  },
}

export default function DemoTutorial({ step, type, onNext, onSkip }) {
  const content = STEPS[step]
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
            <button className="dt-btn-skip" onClick={onSkip}>Skip tutorial</button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="dt-hint">
      <span className="dt-hint-emoji">{content.emoji}</span>
      <div className="dt-hint-body">
        <strong className="dt-hint-title">{content.title}</strong>
        <span className="dt-hint-text"> {content.text}</span>
      </div>
      <button className="dt-hint-close" onClick={onNext} title="Got it">✕</button>
    </div>
  )
}
