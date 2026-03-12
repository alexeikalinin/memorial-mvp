import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { memorialsAPI, invitesAPI, getMediaUrl } from '../api/client'
import MediaGallery from '../components/MediaGallery'
import MemoryList from '../components/MemoryList'
import AvatarChat from '../components/AvatarChat'
import FamilyTree from '../components/FamilyTree'
import LifeTimeline from '../components/LifeTimeline'
import './MemorialDetail.css'

function MemorialDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
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
  const [deleting, setDeleting] = useState(false)

  // Invite modal state
  const [showInviteModal, setShowInviteModal] = useState(false)
  const [inviteLabel, setInviteLabel] = useState('')
  const [creatingInvite, setCreatingInvite] = useState(false)
  const [createdInviteUrl, setCreatedInviteUrl] = useState(null)
  const [inviteList, setInviteList] = useState([])
  const [inviteListLoading, setInviteListLoading] = useState(false)

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

  const handleDelete = async () => {
    if (!confirm(`Удалить мемориал "${memorial.name}"? Это действие нельзя отменить.`)) return
    setDeleting(true)
    try {
      await memorialsAPI.delete(id)
      navigate('/')
    } catch (err) {
      alert(err.response?.data?.detail || 'Ошибка при удалении мемориала')
      setDeleting(false)
    }
  }

  const handleDownloadQR = async () => {
    try {
      const response = await memorialsAPI.getQR(id)
      const url = URL.createObjectURL(response.data)
      const a = document.createElement('a')
      a.href = url
      a.download = `memorial_${id}_qr.png`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      alert('Ошибка при загрузке QR-кода. Убедитесь, что установлен пакет qrcode[pil].')
    }
  }

  const handleSetCover = async (mediaId) => {
    try {
      await memorialsAPI.setCover(id, mediaId)
      await loadMemorial()
    } catch (err) {
      alert(err.response?.data?.detail || 'Ошибка при установке обложки')
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

  const openInviteModal = async () => {
    setShowInviteModal(true)
    setCreatedInviteUrl(null)
    setInviteLabel('')
    setInviteListLoading(true)
    try {
      const res = await invitesAPI.list(id)
      setInviteList(res.data)
    } catch {
      setInviteList([])
    } finally {
      setInviteListLoading(false)
    }
  }

  const handleCreateInvite = async () => {
    setCreatingInvite(true)
    try {
      const res = await invitesAPI.create(id, { label: inviteLabel || null })
      setCreatedInviteUrl(res.data.invite_url)
      setInviteList(prev => [...prev, res.data])
    } catch {
      alert('Ошибка при создании ссылки')
    } finally {
      setCreatingInvite(false)
    }
  }

  const handleRevokeInvite = async (token) => {
    if (!confirm('Отозвать эту ссылку? Она перестанет работать.')) return
    try {
      await invitesAPI.revoke(token)
      setInviteList(prev => prev.filter(i => i.token !== token))
      if (createdInviteUrl && createdInviteUrl.includes(token)) {
        setCreatedInviteUrl(null)
      }
    } catch {
      alert('Ошибка при отзыве ссылки')
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
              <div className="header-actions">
                <button
                  className="btn-edit-header"
                  onClick={() => setEditing(true)}
                  title="Редактировать мемориал"
                >
                  Редактировать
                </button>
                <button
                  className="btn btn-secondary"
                  onClick={handleDownloadQR}
                  title="Скачать QR-код"
                >
                  QR-код
                </button>
                <button
                  className="btn btn-secondary"
                  onClick={openInviteModal}
                  title="Пригласить родственника"
                >
                  Пригласить
                </button>
                <button
                  className="btn btn-danger"
                  onClick={handleDelete}
                  disabled={deleting}
                  title="Удалить мемориал"
                >
                  {deleting ? 'Удаление...' : 'Удалить'}
                </button>
              </div>
            </>
          )}
        </div>
        {!editing && (
          <>
            {memorial.cover_photo_id && (
              <div className="cover-photo-header">
                <img
                  src={getMediaUrl(memorial.cover_photo_id, 'medium')}
                  alt={memorial.name}
                  className="cover-photo-img"
                />
              </div>
            )}
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
        <button
          className={activeTab === 'timeline' ? 'active' : ''}
          onClick={() => setActiveTab('timeline')}
        >
          Хронология
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'media' && (
          <MediaGallery
            memorialId={id}
            onReload={loadMemorial}
            coverPhotoId={memorial.cover_photo_id}
            onSetCover={handleSetCover}
          />
        )}
        {activeTab === 'memories' && (
          <MemoryList memorialId={id} memorialName={memorial.name} onReload={loadMemorial} />
        )}
        {activeTab === 'chat' && (
          <AvatarChat
            memorialId={id}
            coverPhotoId={memorial.cover_photo_id}
            memorialName={memorial.name}
          />
        )}
        {activeTab === 'family' && <FamilyTree memorialId={id} />}
        {activeTab === 'timeline' && <LifeTimeline memorialId={id} />}
      </div>

      {showInviteModal && (
        <div className="modal-overlay" onClick={() => setShowInviteModal(false)}>
          <div className="modal-content invite-modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Пригласить родственника</h3>
              <button className="modal-close" onClick={() => setShowInviteModal(false)}>✕</button>
            </div>

            <div className="invite-form">
              <label>Имя приглашённого (необязательно)</label>
              <input
                type="text"
                value={inviteLabel}
                onChange={e => setInviteLabel(e.target.value)}
                placeholder="Например: Папа, Тётя Маша"
              />
              <button
                className="btn btn-primary"
                onClick={handleCreateInvite}
                disabled={creatingInvite}
              >
                {creatingInvite ? 'Создание...' : 'Создать ссылку'}
              </button>
            </div>

            {createdInviteUrl && (
              <div className="invite-created">
                <p>Ссылка создана:</p>
                <div className="invite-url-row">
                  <code className="invite-url">{createdInviteUrl}</code>
                  <button
                    className="btn-copy"
                    onClick={() => {
                      navigator.clipboard.writeText(createdInviteUrl)
                        .then(() => alert('Ссылка скопирована!'))
                    }}
                  >
                    Копировать
                  </button>
                </div>
              </div>
            )}

            <div className="invite-list-section">
              <h4>Активные ссылки</h4>
              {inviteListLoading ? (
                <p className="invite-list-empty">Загрузка...</p>
              ) : inviteList.length === 0 ? (
                <p className="invite-list-empty">Нет активных ссылок</p>
              ) : (
                <ul className="invite-list">
                  {inviteList.map(inv => (
                    <li key={inv.token} className="invite-item">
                      <span className="invite-item-label">{inv.label || 'Без имени'}</span>
                      <span className="invite-item-uses">{inv.uses_count} переходов</span>
                      <button
                        className="btn-revoke"
                        onClick={() => handleRevokeInvite(inv.token)}
                      >
                        Отозвать
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default MemorialDetail

