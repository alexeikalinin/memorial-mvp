import { useRef, useState, useEffect, useCallback, useId } from 'react'
import { useLanguage } from '../contexts/LanguageContext'

function formatTime(sec) {
  if (!Number.isFinite(sec) || sec < 0) return '0:00'
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

function guessFilename(url) {
  try {
    const path = url.split('?')[0]
    const seg = path.split('/').pop()
    if (seg && /\.(mp3|wav|ogg|m4a|webm)$/i.test(seg)) return seg
  } catch {
    /* ignore */
  }
  return 'audio.mp3'
}

const SPEED_OPTIONS = [0.5, 0.75, 1, 1.25, 1.5, 2]

/**
 * Custom player instead of native audio controls: labels match app language
 * (browser chrome uses OS locale, not app EN). Includes ⋮ menu: download + speed.
 */
export default function ChatAudioPlayer({ src, className = '', downloadName }) {
  const audioRef = useRef(null)
  const menuRef = useRef(null)
  const moreBtnRef = useRef(null)
  const speedId = useId()
  const { t } = useLanguage()
  const [playing, setPlaying] = useState(false)
  const [duration, setDuration] = useState(0)
  const [current, setCurrent] = useState(0)
  const [seeking, setSeeking] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const [playbackRate, setPlaybackRate] = useState(1)

  const filename = downloadName || guessFilename(src)

  const onTimeUpdate = useCallback(() => {
    const a = audioRef.current
    if (!a || seeking) return
    setCurrent(a.currentTime)
  }, [seeking])

  const onLoadedMeta = useCallback(() => {
    const a = audioRef.current
    if (!a) return
    setDuration(a.duration || 0)
  }, [])

  useEffect(() => {
    const a = audioRef.current
    if (!a) return
    setPlaying(false)
    setCurrent(0)
    setDuration(0)
    setPlaybackRate(1)
    a.playbackRate = 1
    a.load()
  }, [src])

  useEffect(() => {
    const a = audioRef.current
    if (a) a.playbackRate = playbackRate
  }, [playbackRate])

  useEffect(() => {
    if (!menuOpen) return
    const onDoc = (e) => {
      const el = menuRef.current
      const btn = moreBtnRef.current
      if (el?.contains(e.target) || btn?.contains(e.target)) return
      setMenuOpen(false)
    }
    document.addEventListener('mousedown', onDoc)
    return () => document.removeEventListener('mousedown', onDoc)
  }, [menuOpen])

  const togglePlay = () => {
    const a = audioRef.current
    if (!a) return
    if (playing) {
      a.pause()
      setPlaying(false)
    } else {
      a.play().then(() => setPlaying(true)).catch(() => setPlaying(false))
    }
  }

  const onSeek = (e) => {
    const a = audioRef.current
    if (!a) return
    const v = parseFloat(e.target.value)
    setSeeking(true)
    setCurrent(v)
    a.currentTime = v
    setSeeking(false)
  }

  const progressMax = duration > 0 ? duration : 1

  return (
    <div className={`chat-audio-custom ${className}`.trim()}>
      <audio
        ref={audioRef}
        src={src}
        preload="metadata"
        onTimeUpdate={onTimeUpdate}
        onLoadedMetadata={onLoadedMeta}
        onEnded={() => { setPlaying(false); setCurrent(0) }}
        onPlay={() => setPlaying(true)}
        onPause={() => setPlaying(false)}
        className="chat-audio-native-hidden"
      >
        {t('chat.browser_no_audio')}
      </audio>
      <div className="chat-audio-custom-inner">
        <button
          type="button"
          className="chat-audio-play"
          onClick={togglePlay}
          aria-label={playing ? t('chat.audio_pause') : t('chat.audio_play')}
        >
          {playing ? '⏸' : '▶'}
        </button>
        <span className="chat-audio-time" aria-hidden="true">
          {formatTime(current)} / {formatTime(duration)}
        </span>
        <input
          type="range"
          className="chat-audio-seek"
          min={0}
          max={progressMax}
          step={0.1}
          value={Math.min(current, progressMax)}
          onChange={onSeek}
          aria-label={t('chat.audio_seek')}
        />
        <div className="chat-audio-more-wrap">
          <button
            type="button"
            ref={moreBtnRef}
            className="chat-audio-more"
            aria-label={t('chat.audio_more')}
            aria-haspopup="true"
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((v) => !v)}
          >
            ⋮
          </button>
          {menuOpen && (
            <div ref={menuRef} className="chat-audio-menu" role="menu">
              <a
                role="menuitem"
                href={src}
                download={filename}
                className="chat-audio-menu-item chat-audio-menu-download"
                onClick={() => setMenuOpen(false)}
              >
                ⬇ {t('chat.audio_download')}
              </a>
              <div className="chat-audio-menu-item chat-audio-menu-speed">
                <label htmlFor={speedId}>{t('chat.audio_speed')}</label>
                <select
                  id={speedId}
                  value={playbackRate}
                  onChange={(e) => {
                    setPlaybackRate(Number(e.target.value))
                    setMenuOpen(false)
                  }}
                >
                  {SPEED_OPTIONS.map((r) => (
                    <option key={r} value={r}>
                      {r === 1 ? '1×' : `${r}×`}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
