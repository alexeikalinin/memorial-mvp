import { useState, useEffect, useRef } from 'react'
import { memorialsAPI, aiAPI } from '../api/client'
import './MemoryList.css'

function MemoryList({ memorialId, onReload }) {
  const [memories, setMemories] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({ title: '', content: '', event_date: '' })
  const [submitting, setSubmitting] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [editFormData, setEditFormData] = useState({ title: '', content: '', event_date: '' })
  const [searchQuery, setSearchQuery] = useState('')
  const [debouncedQuery, setDebouncedQuery] = useState('')

  // Аудио-транскрипция
  const [showAudio, setShowAudio] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [audioBlob, setAudioBlob] = useState(null)
  const [audioUrl, setAudioUrl] = useState(null)
  const [transcribing, setTranscribing] = useState(false)
  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(searchQuery), 300)
    return () => clearTimeout(timer)
  }, [searchQuery])

  useEffect(() => {
    loadMemories(debouncedQuery)
  }, [memorialId, debouncedQuery])

  const startRecording = async () => {
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
      mediaRecorderRef.current = recorder
      setIsRecording(true)
    } catch {
      alert('Нет доступа к микрофону. Разрешите доступ в браузере.')
    }
  }

  const stopRecording = () => {
    mediaRecorderRef.current?.stop()
    setIsRecording(false)
  }

  const handleAudioFileSelect = (e) => {
    const file = e.target.files[0]
    if (!file) return
    setAudioBlob(file)
    setAudioUrl(URL.createObjectURL(file))
  }

  const handleTranscribe = async () => {
    if (!audioBlob) return
    setTranscribing(true)
    try {
      const file = audioBlob instanceof File
        ? audioBlob
        : new File([audioBlob], 'recording.webm', { type: 'audio/webm' })
      const response = await aiAPI.transcribe(file)
      const text = response.data.text
      setFormData((prev) => ({
        ...prev,
        content: prev.content ? prev.content + '\n\n' + text : text,
      }))
      setShowAudio(false)
      setAudioBlob(null)
      setAudioUrl(null)
    } catch (err) {
      alert(err.response?.data?.detail || 'Ошибка при транскрипции')
    } finally {
      setTranscribing(false)
    }
  }

  const resetAudio = () => {
    setAudioBlob(null)
    setAudioUrl(null)
    if (isRecording) {
      mediaRecorderRef.current?.stop()
      setIsRecording(false)
    }
  }

  const loadMemories = async (q = '') => {
    try {
      setLoading(true)
      const response = await memorialsAPI.getMemories(memorialId, q || null)
      setMemories(response.data)
    } catch (err) {
      console.error('Error loading memories:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      const submitData = {
        ...formData,
        event_date: formData.event_date ? `${formData.event_date}T00:00:00Z` : null,
      }
      await memorialsAPI.createMemory(memorialId, submitData)
      setFormData({ title: '', content: '', event_date: '' })
      setShowForm(false)
      await loadMemories(debouncedQuery)
      if (onReload) onReload()
    } catch (err) {
      alert(err.response?.data?.detail || 'Ошибка при добавлении воспоминания')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="memory-list">
      <div className="memory-header">
        <h2>Воспоминания</h2>
        <button
          className="btn btn-primary"
          onClick={() => setShowForm(!showForm)}
        >
          {showForm ? 'Отмена' : 'Добавить воспоминание'}
        </button>
      </div>

      <div className="memory-search">
        <input
          type="text"
          placeholder="Поиск по воспоминаниям..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="search-input"
        />
        {searchQuery && (
          <button className="search-clear" onClick={() => setSearchQuery('')}>✕</button>
        )}
      </div>
      {searchQuery && !loading && (
        <p className="search-results-count">Найдено: {memories.length} воспоминаний</p>
      )}

      {loading && <div className="loading">Загрузка воспоминаний...</div>}

      {showForm && (
        <form onSubmit={handleSubmit} className="memory-form">
          <div className="form-group">
            <label htmlFor="title">Заголовок (опционально)</label>
            <input
              type="text"
              id="title"
              value={formData.title}
              onChange={(e) =>
                setFormData({ ...formData, title: e.target.value })
              }
              placeholder="Краткий заголовок"
            />
          </div>
          <div className="form-group">
            <label htmlFor="content">Текст воспоминания *</label>
            <textarea
              id="content"
              value={formData.content}
              onChange={(e) =>
                setFormData({ ...formData, content: e.target.value })
              }
              rows="6"
              required
              placeholder="Расскажите о человеке, его жизни, характере, важных событиях..."
            />
          </div>

          {/* Аудио-транскрипция */}
          <div className="audio-transcribe-section">
            <button
              type="button"
              className="btn-audio-toggle"
              onClick={() => { setShowAudio(!showAudio); resetAudio() }}
            >
              🎙️ {showAudio ? 'Скрыть' : 'Добавить голосовое воспоминание'}
            </button>

            {showAudio && (
              <div className="audio-controls">
                <p className="audio-hint">
                  Запишите рассказ голосом или загрузите аудиофайл — он будет преобразован в текст и добавлен в воспоминание.
                </p>
                <div className="audio-buttons">
                  {!audioBlob && (
                    <>
                      {!isRecording ? (
                        <button type="button" className="btn-record" onClick={startRecording}>
                          🔴 Начать запись
                        </button>
                      ) : (
                        <button type="button" className="btn-record recording" onClick={stopRecording}>
                          ⏹️ Остановить запись
                        </button>
                      )}
                      <label className="btn-upload-audio">
                        📁 Загрузить аудио
                        <input
                          type="file"
                          accept="audio/*"
                          onChange={handleAudioFileSelect}
                          style={{ display: 'none' }}
                        />
                      </label>
                    </>
                  )}
                  {audioBlob && (
                    <div className="audio-preview">
                      <audio controls src={audioUrl} className="audio-player-small" />
                      <div className="audio-preview-actions">
                        <button
                          type="button"
                          className="btn btn-primary"
                          onClick={handleTranscribe}
                          disabled={transcribing}
                        >
                          {transcribing ? '⏳ Транскрибирую...' : '✍️ Преобразовать в текст'}
                        </button>
                        <button type="button" className="btn btn-secondary" onClick={resetAudio}>
                          Удалить
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="event_date">Когда это было (опционально)</label>
            <input
              type="date"
              id="event_date"
              value={formData.event_date}
              onChange={(e) =>
                setFormData({ ...formData, event_date: e.target.value })
              }
            />
          </div>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={submitting}
          >
            {submitting ? 'Сохранение...' : 'Сохранить'}
          </button>
        </form>
      )}

      {!loading && memories.length === 0 ? (
        <div className="empty-state">
          {searchQuery ? (
            <p>Ничего не найдено по запросу «{searchQuery}»</p>
          ) : (
            <>
              <p>Пока нет добавленных воспоминаний</p>
              <p className="hint">
                Добавьте воспоминания, чтобы ИИ-аватар мог отвечать на вопросы
              </p>
            </>
          )}
        </div>
      ) : !loading && (
        <div className="memories">
          {memories.map((memory) => (
            <div key={memory.id} className="memory-card">
              {editingId === memory.id ? (
                <form
                  onSubmit={async (e) => {
                    e.preventDefault()
                    setSubmitting(true)
                    try {
                      const submitData = {
                        ...editFormData,
                        event_date: editFormData.event_date ? `${editFormData.event_date}T00:00:00Z` : null,
                      }
                      await memorialsAPI.updateMemory(memorialId, memory.id, submitData)
                      setEditingId(null)
                      setEditFormData({ title: '', content: '', event_date: '' })
                      await loadMemories(debouncedQuery)
                      if (onReload) onReload()
                    } catch (err) {
                      alert(err.response?.data?.detail || 'Ошибка при обновлении воспоминания')
                    } finally {
                      setSubmitting(false)
                    }
                  }}
                  className="memory-edit-form"
                >
                  <div className="form-group">
                    <label htmlFor={`edit-title-${memory.id}`}>Заголовок</label>
                    <input
                      type="text"
                      id={`edit-title-${memory.id}`}
                      value={editFormData.title}
                      onChange={(e) =>
                        setEditFormData({ ...editFormData, title: e.target.value })
                      }
                      placeholder="Краткий заголовок"
                    />
                  </div>
                  <div className="form-group">
                    <label htmlFor={`edit-content-${memory.id}`}>Текст *</label>
                    <textarea
                      id={`edit-content-${memory.id}`}
                      value={editFormData.content}
                      onChange={(e) =>
                        setEditFormData({ ...editFormData, content: e.target.value })
                      }
                      rows="6"
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label htmlFor={`edit-event-date-${memory.id}`}>Когда это было</label>
                    <input
                      type="date"
                      id={`edit-event-date-${memory.id}`}
                      value={editFormData.event_date}
                      onChange={(e) =>
                        setEditFormData({ ...editFormData, event_date: e.target.value })
                      }
                    />
                  </div>
                  <div className="form-actions">
                    <button type="submit" className="btn btn-primary" disabled={submitting}>
                      {submitting ? 'Сохранение...' : 'Сохранить'}
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      onClick={() => {
                        setEditingId(null)
                        setEditFormData({ title: '', content: '' })
                      }}
                    >
                      Отмена
                    </button>
                  </div>
                </form>
              ) : (
                <>
                  {memory.title && <h3>{memory.title}</h3>}
                  <p>{memory.content}</p>
                  <div className="memory-meta">
                    {memory.event_date && (
                      <span className="event-date">
                        {new Date(memory.event_date).toLocaleDateString('ru-RU', {
                          year: 'numeric',
                          month: 'long',
                        })}
                      </span>
                    )}
                    <span>
                      Добавлено:{' '}
                      {new Date(memory.created_at).toLocaleDateString('ru-RU')}
                    </span>
                    <div className="memory-actions">
                      <button
                        className="btn-edit"
                        onClick={() => {
                          setEditingId(memory.id)
                          setEditFormData({
                            title: memory.title || '',
                            content: memory.content,
                            event_date: memory.event_date
                              ? new Date(memory.event_date).toISOString().split('T')[0]
                              : '',
                          })
                        }}
                      >
                        ✏️ Редактировать
                      </button>
                      <button
                        className="btn-delete"
                        onClick={async () => {
                          if (confirm('Удалить это воспоминание?')) {
                            try {
                              await memorialsAPI.deleteMemory(memorialId, memory.id)
                              await loadMemories(debouncedQuery)
                              if (onReload) onReload()
                            } catch (err) {
                              alert(err.response?.data?.detail || 'Ошибка при удалении воспоминания')
                            }
                          }
                        }}
                      >
                        🗑️ Удалить
                      </button>
                    </div>
                  </div>
                </>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default MemoryList

