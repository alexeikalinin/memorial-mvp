import { useState, useRef, useEffect } from 'react'
import { aiAPI, memorialsAPI } from '../api/client'
import './AvatarChat.css'

function AvatarChat({ memorialId }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [includeAudio, setIncludeAudio] = useState(false)
  const [uploadingVoice, setUploadingVoice] = useState(false)
  const [voiceName, setVoiceName] = useState('')
  const [hasCustomVoice, setHasCustomVoice] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    // Проверяем, есть ли кастомный голос у мемориала
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

    setUploadingVoice(true)
    try {
      const response = await aiAPI.uploadVoice(memorialId, file, voiceName || undefined)
      alert(response.data.message || 'Голос успешно загружен!')
      setHasCustomVoice(true)
      setVoiceName('')
      e.target.value = '' // Сброс input
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Ошибка при загрузке голоса'
      alert(errorMsg)
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
      })

      const assistantMessage = {
        role: 'assistant',
        text: response.data.answer,
        audioUrl: response.data.audio_url,
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

  return (
    <div className="avatar-chat">
      <div className="chat-header">
        <h2>Чат с ИИ-аватаром</h2>
        <div className="header-controls">
          <label className="audio-toggle">
            <input
              type="checkbox"
              checked={includeAudio}
              onChange={(e) => setIncludeAudio(e.target.checked)}
            />
            Генерировать аудио
          </label>
          <div className="voice-upload-section">
            {hasCustomVoice ? (
              <span className="voice-status">✅ Кастомный голос загружен</span>
            ) : (
              <label className="voice-upload-btn">
                {uploadingVoice ? 'Загрузка...' : '📤 Загрузить голос'}
                <input
                  type="file"
                  accept="audio/*"
                  onChange={handleVoiceUpload}
                  disabled={uploadingVoice}
                  style={{ display: 'none' }}
                />
              </label>
            )}
            {!hasCustomVoice && (
              <input
                type="text"
                placeholder="Имя голоса (опционально)"
                value={voiceName}
                onChange={(e) => setVoiceName(e.target.value)}
                className="voice-name-input"
                disabled={uploadingVoice}
              />
            )}
          </div>
        </div>
      </div>

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="welcome-message">
            <p>Задайте вопрос об этом человеке, и ИИ-аватар ответит на основе добавленных воспоминаний.</p>
            <p className="hint">Например: "Расскажи о детстве этого человека"</p>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <div className="message-content">
              <p>{msg.text}</p>
              {msg.audioUrl && (
                <div className="audio-container">
                  <audio 
                    controls 
                    src={msg.audioUrl.startsWith('http') ? msg.audioUrl : `http://localhost:8000${msg.audioUrl}`}
                    className="audio-player"
                    preload="metadata"
                  >
                    Ваш браузер не поддерживает аудио.
                  </audio>
                </div>
              )}
              {msg.sources && msg.sources.length > 0 && (
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

