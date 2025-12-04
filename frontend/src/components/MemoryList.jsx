import { useState, useEffect } from 'react'
import { memorialsAPI } from '../api/client'
import './MemoryList.css'

function MemoryList({ memorialId, onReload }) {
  const [memories, setMemories] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({ title: '', content: '' })
  const [submitting, setSubmitting] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [editFormData, setEditFormData] = useState({ title: '', content: '' })

  useEffect(() => {
    loadMemories()
  }, [memorialId])

  const loadMemories = async () => {
    try {
      setLoading(true)
      const response = await memorialsAPI.getMemories(memorialId)
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
      await memorialsAPI.createMemory(memorialId, formData)
      setFormData({ title: '', content: '' })
      setShowForm(false)
      await loadMemories()
      if (onReload) onReload()
    } catch (err) {
      alert(err.response?.data?.detail || 'Ошибка при добавлении воспоминания')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return <div className="loading">Загрузка воспоминаний...</div>
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
          <button
            type="submit"
            className="btn btn-primary"
            disabled={submitting}
          >
            {submitting ? 'Сохранение...' : 'Сохранить'}
          </button>
        </form>
      )}

      {memories.length === 0 ? (
        <div className="empty-state">
          <p>Пока нет добавленных воспоминаний</p>
          <p className="hint">
            Добавьте воспоминания, чтобы ИИ-аватар мог отвечать на вопросы
          </p>
        </div>
      ) : (
        <div className="memories">
          {memories.map((memory) => (
            <div key={memory.id} className="memory-card">
              {editingId === memory.id ? (
                <form
                  onSubmit={async (e) => {
                    e.preventDefault()
                    setSubmitting(true)
                    try {
                      await memorialsAPI.updateMemory(memorialId, memory.id, editFormData)
                      setEditingId(null)
                      setEditFormData({ title: '', content: '' })
                      await loadMemories()
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
                              await loadMemories()
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

