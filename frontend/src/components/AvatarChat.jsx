import { useState, useRef, useEffect } from 'react'
import { aiAPI, memorialsAPI, getMediaUrl } from '../api/client'
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
      alert('Нет доступа к микрофону.')
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

const SUGGESTED_QUESTIONS = [
  'Расскажи о своём детстве',
  'Что ты любил больше всего в жизни?',
  'Расскажи о своей семье',
  'Какое твоё самое яркое воспоминание?',
  'Какой совет ты бы дал своим близким?',
]

function AvatarChat({ memorialId, coverPhotoId, memorialName }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [includeAudio, setIncludeAudio] = useState(false)
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
      })

      const assistantMessage = {
        role: 'assistant',
        text: response.data.answer,
        audioUrl: response.data.audio_url,
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
        text: err.response?.data?.detail || err.message || 'Ошибка при отправке сообщения',
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
    if (confirm('Очистить историю чата?')) {
      setMessages([])
      localStorage.removeItem(storageKey)
    }
  }

  const handleSyncFamily = async () => {
    if (!confirm('Запустить синхронизацию воспоминаний с родственниками? Это создаст новые воспоминания в мемориалах родственников на основе текстов этого мемориала.')) return
    setSyncing(true)
    try {
      const res = await aiAPI.syncFamilyMemories(memorialId)
      const { created, skipped } = res.data
      alert(`Синхронизация завершена. Создано: ${created}, пропущено: ${skipped}.`)
    } catch (err) {
      alert(err.response?.data?.detail || 'Ошибка при синхронизации')
    } finally {
      setSyncing(false)
    }
  }

  return (
    <div className={`avatar-chat${isFullscreen ? ' avatar-chat--fullscreen' : ''}`}>
      <div className="chat-header">
        <div className="chat-header-title">
          {coverPhotoId ? (
            <img
              src={getMediaUrl(coverPhotoId, 'small')}
              alt={memorialName || 'Аватар'}
              className="chat-avatar-img"
            />
          ) : (
            <div className="chat-avatar-placeholder">
              {memorialName ? memorialName[0].toUpperCase() : '?'}
            </div>
          )}
          <h2>{memorialName ? `Чат с ${memorialName}` : 'Чат с ИИ-аватаром'}</h2>
        </div>
        <div className="header-controls">
          <label className="audio-toggle">
            <input
              type="checkbox"
              checked={includeAudio}
              onChange={(e) => setIncludeAudio(e.target.checked)}
            />
            Генерировать аудио
          </label>
          <label className="audio-toggle family-memories-toggle">
            <input
              type="checkbox"
              checked={includeFamilyMemories}
              onChange={(e) => setIncludeFamilyMemories(e.target.checked)}
            />
            Воспоминания родственников
            <span className="info-trigger" title="Подсказка" tabIndex={0}>?</span>
            <span className="info-tooltip">
              <strong>Галочка включена:</strong> ответы ищутся и по воспоминаниям этого человека, и по воспоминаниям родственников (из их мемориалов), где он упоминается.
              <br />
              <strong>Галочка выключена:</strong> используются только воспоминания выбранного члена семьи.
            </span>
          </label>
          <button
            className="btn-clear-history"
            onClick={handleSyncFamily}
            disabled={syncing}
            title="Синхронизировать воспоминания с семьёй"
          >
            {syncing ? '⏳ Синхронизация...' : '🔄 Синхр. с семьёй'}
          </button>
          <button
            className="btn-fullscreen"
            onClick={() => setIsFullscreen((v) => !v)}
            title={isFullscreen ? 'Свернуть' : 'На весь экран'}
          >
            {isFullscreen ? '⛶' : '⛶'}
            {isFullscreen ? 'Свернуть' : 'На весь экран'}
          </button>
          {messages.length > 0 && (
            <button className="btn-clear-history" onClick={handleClearHistory} title="Очистить историю">
              Очистить историю
            </button>
          )}
          <div className="voice-clone-section">
            {hasCustomVoice ? (
              <div className="voice-status-row">
                <span className="voice-status">✅ Голос аватара загружен</span>
                <button
                  className="btn-voice-change"
                  onClick={() => { setHasCustomVoice(false); setShowVoicePanel(true) }}
                >
                  Изменить
                </button>
              </div>
            ) : (
              <button
                className="btn-voice-clone"
                onClick={() => setShowVoicePanel(!showVoicePanel)}
              >
                🎤 Клонировать голос аватара
              </button>
            )}
          </div>
        </div>
      </div>

      {showVoicePanel && (
        <div className="voice-clone-panel">
          <div className="voice-clone-panel-header">
            <h3>🎤 Клон голоса аватара</h3>
            <button className="btn-close-panel" onClick={() => { setShowVoicePanel(false); voiceRecorder.reset() }}>✕</button>
          </div>
          <p className="voice-clone-hint">
            Аватар будет отвечать голосом этого человека. Нужна минимум 1 минута чистой речи без шума.
          </p>
          <div className="voice-clone-name">
            <input
              type="text"
              placeholder="Имя голоса (опционально)"
              value={voiceName}
              onChange={(e) => setVoiceName(e.target.value)}
              disabled={uploadingVoice}
            />
          </div>
          <div className="voice-clone-options">
            <div className="voice-clone-option">
              <p className="option-label">Записать прямо сейчас <span className="option-hint">(если человек жив)</span>:</p>
              {!voiceRecorder.audioBlob ? (
                <div className="record-controls">
                  {!voiceRecorder.isRecording ? (
                    <button type="button" className="btn-record" onClick={voiceRecorder.start} disabled={uploadingVoice}>
                      🔴 Начать запись
                    </button>
                  ) : (
                    <button type="button" className="btn-record recording" onClick={voiceRecorder.stop}>
                      ⏹️ Остановить
                    </button>
                  )}
                  {voiceRecorder.isRecording && <span className="rec-indicator">● REC</span>}
                </div>
              ) : (
                <div className="audio-preview">
                  <audio controls src={voiceRecorder.audioUrl} className="audio-player-small" />
                  <div className="audio-preview-actions">
                    <button
                      type="button"
                      className="btn btn-primary"
                      onClick={handleVoiceRecordedUpload}
                      disabled={uploadingVoice}
                    >
                      {uploadingVoice ? '⏳ Клонирование...' : '✅ Использовать эту запись'}
                    </button>
                    <button type="button" className="btn btn-secondary" onClick={voiceRecorder.reset}>
                      Перезаписать
                    </button>
                  </div>
                </div>
              )}
            </div>
            <div className="voice-clone-divider">или</div>
            <div className="voice-clone-option">
              <p className="option-label">Загрузить запись <span className="option-hint">(если голос сохранился)</span>:</p>
              <p className="option-sublabel">MP3, WAV, M4A</p>
              <label className="btn-upload-voice">
                {uploadingVoice ? '⏳ Клонирование...' : '📁 Выбрать файл'}
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
            <p>Задайте вопрос об этом человеке, и ИИ-аватар ответит на основе добавленных воспоминаний.</p>
            <div className="suggested-questions">
              <p className="suggested-label">Попробуйте спросить:</p>
              <div className="suggested-list">
                {SUGGESTED_QUESTIONS.map((q, i) => (
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
                  <img
                    src={getMediaUrl(coverPhotoId, 'small')}
                    alt={memorialName || 'Аватар'}
                    className="message-avatar-img"
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
                    Ваш браузер не поддерживает видео.
                  </video>
                </div>
              ) : msg.videoStatus === 'pending' ? (
                <div className="video-loading">
                  <span className="video-loading-icon">🎬</span> Видео генерируется...
                </div>
              ) : msg.audioUrl ? (
                <div className="audio-container">
                  <audio
                    controls
                    src={msg.audioUrl}
                    className="audio-player"
                    preload="metadata"
                  >
                    Ваш браузер не поддерживает аудио.
                  </audio>
                </div>
              ) : null}
              {Array.isArray(msg.sources) && msg.sources.length > 0 && (
                <div className="sources">
                  <strong>Источники:</strong>
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
          placeholder="Задайте вопрос..."
          disabled={loading}
          className="chat-input"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="send-btn"
        >
          Отправить
        </button>
      </form>
    </div>
  )
}

export default AvatarChat
