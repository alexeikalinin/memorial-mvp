import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { memorialsAPI, aiAPI, mediaAPI } from '../api/client'
import MediaGallery from '../components/MediaGallery'
import MemoryList from '../components/MemoryList'
import AvatarChat from '../components/AvatarChat'
import FamilyTree from '../components/FamilyTree'
import './MemorialDetail.css'

function MemorialDetail() {
  const { id } = useParams()
  const [memorial, setMemorial] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('media')
  const [editing, setEditing] = useState(false)
  const [editFormData, setEditFormData] = useState({
    name: '',
    description: '',
    birth_date: '',
    death_date: '',
    is_public: false,
  })
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    loadMemorial()
  }, [id])

  const loadMemorial = async () => {
    try {
      setLoading(true)
      const response = await memorialsAPI.get(id)
      setMemorial(response.data)
      // Заполняем форму редактирования
      setEditFormData({
        name: response.data.name || '',
        description: response.data.description || '',
        birth_date: response.data.birth_date
          ? new Date(response.data.birth_date).toISOString().split('T')[0]
          : '',
        death_date: response.data.death_date
          ? new Date(response.data.death_date).toISOString().split('T')[0]
          : '',
        is_public: response.data.is_public || false,
      })
    } catch (err) {
      setError(err.response?.data?.detail || 'Ошибка при загрузке мемориала')
    } finally {
      setLoading(false)
    }
  }

  const handleUpdate = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      const submitData = {
        ...editFormData,
        birth_date: editFormData.birth_date ? `${editFormData.birth_date}T00:00:00Z` : null,
        death_date: editFormData.death_date ? `${editFormData.death_date}T00:00:00Z` : null,
      }
      await memorialsAPI.update(id, submitData)
      setEditing(false)
      await loadMemorial()
    } catch (err) {
      const errorData = err.response?.data
      if (errorData?.detail) {
        if (Array.isArray(errorData.detail)) {
          const errorMessages = errorData.detail.map((err) => {
            const field = err.loc?.join('.') || 'поле'
            return `${field}: ${err.msg}`
          })
          alert(errorMessages.join('\n'))
        } else {
          alert(errorData.detail)
        }
      } else {
        alert('Ошибка при обновлении мемориала')
      }
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return <div className="loading">Загрузка...</div>
  }

  if (error || !memorial) {
    return <div className="error-message">{error || 'Мемориал не найден'}</div>
  }

  return (
    <div className="memorial-detail">
      <div className="memorial-header">
        <div className="header-top">
          {editing ? (
            <form onSubmit={handleUpdate} className="edit-form">
              <div className="form-group">
                <label htmlFor="name">Имя *</label>
                <input
                  type="text"
                  id="name"
                  value={editFormData.name}
                  onChange={(e) =>
                    setEditFormData({ ...editFormData, name: e.target.value })
                  }
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="description">Описание</label>
                <textarea
                  id="description"
                  value={editFormData.description}
                  onChange={(e) =>
                    setEditFormData({ ...editFormData, description: e.target.value })
                  }
                  rows="3"
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="birth_date">Дата рождения</label>
                  <input
                    type="date"
                    id="birth_date"
                    value={editFormData.birth_date}
                    onChange={(e) =>
                      setEditFormData({ ...editFormData, birth_date: e.target.value })
                    }
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="death_date">Дата смерти</label>
                  <input
                    type="date"
                    id="death_date"
                    value={editFormData.death_date}
                    onChange={(e) =>
                      setEditFormData({ ...editFormData, death_date: e.target.value })
                    }
                  />
                </div>
              </div>
              <div className="form-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={editFormData.is_public}
                    onChange={(e) =>
                      setEditFormData({ ...editFormData, is_public: e.target.checked })
                    }
                  />
                  Публичный мемориал
                </label>
              </div>
              <div className="form-actions">
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? 'Сохранение...' : 'Сохранить'}
                </button>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => {
                    setEditing(false)
                    loadMemorial() // Восстанавливаем исходные данные
                  }}
                >
                  Отмена
                </button>
              </div>
            </form>
          ) : (
            <>
              <h1>{memorial.name}</h1>
              <button
                className="btn-edit-header"
                onClick={() => setEditing(true)}
                title="Редактировать мемориал"
              >
                ✏️
              </button>
            </>
          )}
        </div>
        {!editing && (
          <>
            {memorial.description && <p className="description">{memorial.description}</p>}
            {(memorial.birth_date || memorial.death_date) && (
              <div className="dates">
                {memorial.birth_date && (
                  <span>Родился: {new Date(memorial.birth_date).toLocaleDateString('ru-RU')}</span>
                )}
                {memorial.death_date && (
                  <span>Умер: {new Date(memorial.death_date).toLocaleDateString('ru-RU')}</span>
                )}
              </div>
            )}
          </>
        )}
      </div>

      <div className="tabs">
        <button
          className={activeTab === 'media' ? 'active' : ''}
          onClick={() => setActiveTab('media')}
        >
          Медиа
        </button>
        <button
          className={activeTab === 'memories' ? 'active' : ''}
          onClick={() => setActiveTab('memories')}
        >
          Воспоминания
        </button>
        <button
          className={activeTab === 'chat' ? 'active' : ''}
          onClick={() => setActiveTab('chat')}
        >
          Чат с аватаром
        </button>
        <button
          className={activeTab === 'family' ? 'active' : ''}
          onClick={() => setActiveTab('family')}
        >
          Семейное дерево
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'media' && (
          <MediaGallery memorialId={id} onReload={loadMemorial} />
        )}
        {activeTab === 'memories' && (
          <MemoryList memorialId={id} onReload={loadMemorial} />
        )}
        {activeTab === 'chat' && <AvatarChat memorialId={id} />}
        {activeTab === 'family' && <FamilyTree memorialId={id} />}
      </div>
    </div>
  )
}

export default MemorialDetail

