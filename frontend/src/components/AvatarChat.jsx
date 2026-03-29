import { useState, useRef, useEffect } from 'react'
import { aiAPI, memorialsAPI } from '../api/client'
import ApiMediaImage from './ApiMediaImage'
import ChatAudioPlayer from './ChatAudioPlayer'
import { instrumentalName } from '../utils/declension'
import { useLanguage } from '../contexts/LanguageContext'
import './AvatarChat.css'

// Запись аудио для клона голоса
function useVoiceRecorder() {
  const [isRecording, setIsRecording] = useState(false)
  const [audioBlob, setAudioBlob] = useState(null)
  const [audioUrl, setAudioUrl] = useState(null)
  const recorderRef = useRef(null)
  const chunksRef = useRef([])

  const start = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' })
      chunksRef.current = []
      recorder.ondataavailable = (e) => chunksRef.current.push(e.data)
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        setAudioBlob(blob)
        setAudioUrl(URL.createObjectURL(blob))
        stream.getTracks().forEach((t) => t.stop())
      }
      recorder.start()
      recorderRef.current = recorder
      setIsRecording(true)
    } catch {
      alert('Microphone access denied.')
    }
  }

  const stop = () => {
    recorderRef.current?.stop()
    setIsRecording(false)
  }

  const reset = () => {
    setAudioBlob(null)
    setAudioUrl(null)
    if (isRecording) { recorderRef.current?.stop(); setIsRecording(false) }
  }

  return { isRecording, audioBlob, audioUrl, start, stop, reset }
}

/** URL, по которому браузер может воспроизвести аудио (никогда s3://, голый filename превращаем в /api/v1/media/audio/...) */
function getPlayableAudioUrl(url) {
  if (!url) return null
  if (url.startsWith('s3://')) return null
  if (/^https?:\/\//.test(url) || url.startsWith('/')) return url
  const base = (import.meta.env.VITE_API_URL || '/api/v1').replace(/\/$/, '')
  return `${base}/media/audio/${url}`
}

function AvatarChat({ memorialId, coverPhotoId, memorialName }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [includeAudio, setIncludeAudio] = useState(true)
  const { lang, t } = useLanguage()
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [includeFamilyMemories, setIncludeFamilyMemories] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [uploadingVoice, setUploadingVoice] = useState(false)
  const [voiceName, setVoiceName] = useState('')
  const [hasCustomVoice, setHasCustomVoice] = useState(false)
  const [showVoicePanel, setShowVoicePanel] = useState(false)
  const messagesEndRef = useRef(null)
  const voiceRecorder = useVoiceRecorder()

  const storageKey = `chat_${memorialId}`

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Load chat history from localStorage
  useEffect(() => {
    try {
      const saved = localStorage.getItem(storageKey)
      if (saved) {
        const parsed = JSON.parse(saved)
        setMessages(Array.isArray(parsed) ? parsed : [])
      }
    } catch (e) {
      // ignore corrupt data
    }
  }, [memorialId])

  // Save chat history to localStorage whenever messages change
  useEffect(() => {
    if (messages.length > 0) {
      try {
        localStorage.setItem(storageKey, JSON.stringify(messages))
      } catch (e) {
        // ignore storage errors
      }
    }
  }, [messages, storageKey])

  // Polling анимации: каждые 5 сек проверяем статус для pending сообщений
  useEffect(() => {
    const pendingMessages = messages.filter(
      (m) => m.role === 'assistant' && m.animationTaskId && m.videoStatus === 'pending'
    )
    if (pendingMessages.length === 0) return

    const interval = setInterval(async () => {
      for (const msg of pendingMessages) {
        try {
          const res = await aiAPI.getAnimationStatus({
            task_id: msg.animationTaskId,
            provider: msg.animationProvider,
          })
          const { status, video_url } = res.data
          if (status === 'completed' && video_url) {
            setMessages((prev) =>
              prev.map((m) =>
                m.animationTaskId === msg.animationTaskId
                  ? { ...m, videoUrl: video_url, videoStatus: 'ready' }
                  : m
              )
            )
          } else if (status === 'error' || status === 'failed') {
            setMessages((prev) =>
              prev.map((m) =>
                m.animationTaskId === msg.animationTaskId
                  ? { ...m, videoStatus: 'error' }
                  : m
              )
            )
          }
        } catch (err) {
          console.warn('Animation status poll error:', err)
        }
      }
    }, 5000)

    return () => clearInterval(interval)
  }, [messages])

  useEffect(() => {
    const checkVoice = async () => {
      try {
        const response = await memorialsAPI.get(memorialId)
        setHasCustomVoice(!!response.data.voice_id)
      } catch (err) {
        console.error('Error checking voice:', err)
      }
    }
    checkVoice()
  }, [memorialId])

  const handleVoiceUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    if (!file.type.startsWith('audio/')) {
      alert('Пожалуйста, выберите аудио файл (MP3, WAV, M4A)')
      return
    }
    await uploadVoiceFile(file)
    e.target.value = ''
  }

  const handleVoiceRecordedUpload = async () => {
    if (!voiceRecorder.audioBlob) return
    const file = new File([voiceRecorder.audioBlob], 'voice_clone.webm', { type: 'audio/webm' })
    await uploadVoiceFile(file)
    voiceRecorder.reset()
  }

  const uploadVoiceFile = async (file) => {
    setUploadingVoice(true)
    try {
      const response = await aiAPI.uploadVoice(memorialId, file, voiceName || undefined)
      alert(response.data.message || 'Голос успешно клонирован!')
      setHasCustomVoice(true)
      setVoiceName('')
      setShowVoicePanel(false)
    } catch (err) {
      const status = err.response?.status
      const detail = err.response?.data?.detail || 'Ошибка при клонировании голоса'
      if (status === 402) {
        alert(`⚠️ ${detail}`)
      } else {
        alert(detail)
      }
    } finally {
      setUploadingVoice(false)
    }
  }

  const handleSend = async (e) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')
    setMessages((prev) => [...prev, { role: 'user', text: userMessage }])
    setLoading(true)

    try {
      const response = await aiAPI.chat({
        memorial_id: parseInt(memorialId),
        question: userMessage,
        include_audio: includeAudio,
        include_family_memories: includeFamilyMemories,
        language: lang,
      })

      // Браузер воспроизводит только http(s) или относительный /api/...; s3:// и голый filename — нормализуем
      let audioUrl = response.data.audio_url || null
      if (audioUrl) {
        if (audioUrl.startsWith('s3://')) audioUrl = null
        else if (!/^https?:\/\//.test(audioUrl) && !audioUrl.startsWith('/')) {
          const base = (import.meta.env.VITE_API_URL || '/api/v1').replace(/\/$/, '')
          audioUrl = `${base}/media/audio/${audioUrl}`
        }
      }

      const assistantMessage = {
        role: 'assistant',
        text: response.data.answer,
        audioUrl,
        audioError: response.data.audio_error || null,
        animationTaskId: response.data.animation_task_id || null,
        animationProvider: response.data.animation_provider || null,
        videoUrl: null,
        videoStatus: response.data.animation_task_id ? 'pending' : null,
        sources: response.data.sources || [],
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (err) {
      console.error('Chat error:', err)
      const errorMessage = {
        role: 'error',
        text: err.response?.data?.detail || err.message || t('chat.chat_error'),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleSuggestedQuestion = (question) => {
    setInput(question)
  }

  const handleClearHistory = () => {
    if (!confirm(t('chat.clear_confirm'))) return
    setMessages([])
    localStorage.removeItem(storageKey)
  }

  const handleSyncFamily = async () => {
    if (!confirm(t('chat.sync_confirm'))) return
    setSyncing(true)
    try {
      const res = await aiAPI.syncFamilyMemories(memorialId)
      const { created, skipped } = res.data
      alert(t('chat.sync_done', { created: String(created), skipped: String(skipped) }))
    } catch (err) {
      alert(err.response?.data?.detail || t('chat.sync_error'))
    } finally {
      setSyncing(false)
    }
  }

  return (
    <div className={`avatar-chat${isFullscreen ? ' avatar-chat--fullscreen' : ''}`}>
      {/* ─── Left: Avatar panel ──────────────────────────────────── */}
      <div className="avatar-panel">
        {coverPhotoId ? (
          <ApiMediaImage
            mediaId={coverPhotoId}
            thumbnail="medium"
            alt={memorialName || 'Avatar'}
            className="avatar-panel-photo"
            fallback={
              <div className="avatar-panel-placeholder">
                <span>{memorialName ? memorialName[0].toUpperCase() : '?'}</span>
              </div>
            }
          />
        ) : (
          <div className="avatar-panel-placeholder">
            <span>{memorialName ? memorialName[0].toUpperCase() : '?'}</span>
          </div>
        )}
        {loading && (
          <div className="avatar-thinking-overlay">
            <span></span><span></span><span></span>
          </div>
        )}
        <div className="avatar-panel-footer">
          {memorialName && (
            <div className="avatar-panel-name">{memorialName}</div>
          )}
          <div className="avatar-panel-status">
            <span className={`avatar-status-dot${loading ? ' avatar-status-dot--active' : ''}`}></span>
            <span className="avatar-status-text">
              {loading ? t('chat.avatar_thinking') : t('chat.avatar_ready')}
            </span>
          </div>
        </div>
      </div>

      {/* ─── Right: Chat panel ───────────────────────────────────── */}
      <div className="chat-panel">
      <div className="chat-header">
        <div className="chat-header-title">
          <h2>
            {memorialName
              ? lang === 'en'
                ? t('chat.title_with', { name: memorialName })
                : `Чат с ${instrumentalName(memorialName)}`
              : t('chat.title_default')}
          </h2>
        </div>
        <div className="header-controls">
          <label className="audio-toggle">
            <input
              type="checkbox"
              checked={includeAudio}
              onChange={(e) => setIncludeAudio(e.target.checked)}
            />
            {t('chat.audio_label')}
          </label>
          <label className="audio-toggle family-memories-toggle">
            <input
              type="checkbox"
              checked={includeFamilyMemories}
              onChange={(e) => setIncludeFamilyMemories(e.target.checked)}
            />
            {t('chat.family_label')}
            <span className="info-trigger" title={t('chat.family_tooltip_title')} tabIndex={0}>?</span>
            <span className="info-tooltip">
              {t('chat.family_tooltip_on')}
              <br /><br />
              {t('chat.family_tooltip_off')}
            </span>
          </label>
          <button
            className="btn-clear-history"
            onClick={handleSyncFamily}
            disabled={syncing}
            title={t('chat.sync_family')}
          >
            {syncing ? `⏳ ${t('chat.syncing')}` : `🔄 ${t('chat.sync_family')}`}
          </button>
          <button
            className="btn-fullscreen"
            onClick={() => setIsFullscreen((v) => !v)}
            title={isFullscreen ? t('chat.exit_fullscreen') : t('chat.fullscreen')}
          >
            {isFullscreen ? '⛶' : '⛶'}
            {isFullscreen ? t('chat.exit_fullscreen') : t('chat.fullscreen')}
          </button>
          {messages.length > 0 && (
            <button className="btn-clear-history" onClick={handleClearHistory} title={t('chat.clear_history')}>
              {t('chat.clear_history')}
            </button>
          )}
          <div className="voice-clone-section">
            {hasCustomVoice ? (
              <div className="voice-status-row">
                <span className="voice-status">✅ {t('chat.voice_uploaded')}</span>
                <button
                  className="btn-voice-change"
                  onClick={() => { setHasCustomVoice(false); setShowVoicePanel(true) }}
                >
                  {t('chat.voice_change')}
                </button>
              </div>
            ) : (
              <button
                className="btn-voice-clone"
                onClick={() => setShowVoicePanel(!showVoicePanel)}
              >
                🎤 {t('chat.voice_clone')}
              </button>
            )}
          </div>
        </div>
      </div>

      {showVoicePanel && (
        <div className="voice-clone-panel">
          <div className="voice-clone-panel-header">
            <h3>🎤 {t('chat.voice_panel_title')}</h3>
            <button type="button" className="btn-close-panel" onClick={() => { setShowVoicePanel(false); voiceRecorder.reset() }} aria-label={t('chat.voice_panel_close')}>✕</button>
          </div>
          <p className="voice-clone-hint">
            {t('chat.voice_hint')}
          </p>
          <div className="voice-clone-name">
            <input
              type="text"
              placeholder={t('chat.voice_name_placeholder')}
              value={voiceName}
              onChange={(e) => setVoiceName(e.target.value)}
              disabled={uploadingVoice}
            />
          </div>
          <div className="voice-clone-options">
            <div className="voice-clone-option">
              <p className="option-label">{t('chat.voice_record_now')} <span className="option-hint">{t('chat.voice_if_alive')}</span>:</p>
              {!voiceRecorder.audioBlob ? (
                <div className="record-controls">
                  {!voiceRecorder.isRecording ? (
                    <button type="button" className="btn-record" onClick={voiceRecorder.start} disabled={uploadingVoice}>
                      🔴 {t('chat.voice_record_start')}
                    </button>
                  ) : (
                    <button type="button" className="btn-record recording" onClick={voiceRecorder.stop}>
                      ⏹️ {t('chat.voice_record_stop')}
                    </button>
                  )}
                  {voiceRecorder.isRecording && <span className="rec-indicator">{t('chat.rec_indicator')}</span>}
                </div>
              ) : (
                <div className="audio-preview">
                  <ChatAudioPlayer src={voiceRecorder.audioUrl} className="audio-player-small" />
                  <div className="audio-preview-actions">
                    <button
                      type="button"
                      className="btn btn-primary"
                      onClick={handleVoiceRecordedUpload}
                      disabled={uploadingVoice}
                    >
                      {uploadingVoice ? `⏳ ${t('chat.voice_cloning')}` : `✅ ${t('chat.voice_use_recording')}`}
                    </button>
                    <button type="button" className="btn btn-secondary" onClick={voiceRecorder.reset}>
                      {t('chat.voice_rerecord')}
                    </button>
                  </div>
                </div>
              )}
            </div>
            <div className="voice-clone-divider">{t('chat.voice_or')}</div>
            <div className="voice-clone-option">
              <p className="option-label">{t('chat.voice_upload_label')} <span className="option-hint">{t('chat.voice_upload_hint')}</span>:</p>
              <p className="option-sublabel">MP3, WAV, M4A</p>
              <label className="btn-upload-voice">
                {uploadingVoice ? `⏳ ${t('chat.voice_cloning')}` : `📁 ${t('chat.voice_choose_file')}`}
                <input
                  type="file"
                  accept="audio/*"
                  onChange={handleVoiceUpload}
                  disabled={uploadingVoice}
                  style={{ display: 'none' }}
                />
              </label>
            </div>
          </div>
        </div>
      )}

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="welcome-message">
            <p>{t('chat.welcome_intro')}</p>
            <div className="suggested-questions">
              <p className="suggested-label">{t('chat.suggested_label')}</p>
              <div className="suggested-list">
                {t('chat.questions').map((q, i) => (
                  <button
                    key={i}
                    className="suggested-btn"
                    onClick={() => handleSuggestedQuestion(q)}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {(Array.isArray(messages) ? messages : []).map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            {msg.role === 'assistant' && (
              <div className="message-avatar">
                {coverPhotoId ? (
                  <ApiMediaImage
                    mediaId={coverPhotoId}
                    thumbnail="small"
                    alt={memorialName || 'Avatar'}
                    className="message-avatar-img"
                    fallback={
                      <div className="message-avatar-placeholder">
                        {memorialName ? memorialName[0].toUpperCase() : '?'}
                      </div>
                    }
                  />
                ) : (
                  <div className="message-avatar-placeholder">
                    {memorialName ? memorialName[0].toUpperCase() : '?'}
                  </div>
                )}
              </div>
            )}
            <div className="message-content">
              <p>{msg.text}</p>
              {msg.videoUrl ? (
                <div className="video-container">
                  <video
                    controls
                    autoPlay
                    src={msg.videoUrl}
                    className="avatar-video"
                  >
                    {t('chat.browser_no_video')}
                  </video>
                </div>
              ) : msg.videoStatus === 'pending' ? (
                <div className="video-loading">
                  <span className="video-loading-icon">🎬</span> {t('chat.video_generating')}
                </div>
              ) : getPlayableAudioUrl(msg.audioUrl) ? (
                <div className="audio-container">
                  <ChatAudioPlayer
                    src={getPlayableAudioUrl(msg.audioUrl)}
                    className="audio-player"
                  />
                </div>
              ) : msg.audioError ? (
                <div className="audio-error">
                  {t('chat.audio_failed')} {msg.audioError}
                </div>
              ) : null}
              {Array.isArray(msg.sources) && msg.sources.length > 0 && (
                <div className="sources">
                  <strong>{t('chat.sources')}</strong>
                  <ul>
                    {msg.sources.map((source, i) => (
                      <li key={i}>{source}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="message assistant">
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSend} className="chat-input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={t('chat.placeholder')}
          disabled={loading}
          className="chat-input"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="send-btn"
        >
          {t('chat.send')}
        </button>
      </form>
      </div>{/* end .chat-panel */}
    </div>
  )
}

export default AvatarChat
