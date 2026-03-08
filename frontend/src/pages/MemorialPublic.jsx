import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { memorialsAPI, getMediaUrl } from '../api/client'
import AvatarChat from '../components/AvatarChat'
import './MemorialPublic.css'

function MemorialPublic() {
  const { id } = useParams()
  const [memorial, setMemorial] = useState(null)
  const [memories, setMemories] = useState([])
  const [photos, setPhotos] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeSection, setActiveSection] = useState('chat')

  useEffect(() => {
    const loadData = async () => {
      try {
        const [memRes, memoriesRes, mediaRes] = await Promise.all([
          memorialsAPI.get(id),
          memorialsAPI.getMemories(id),
          memorialsAPI.getMedia(id),
        ])
        setMemorial(memRes.data)
        setMemories(memoriesRes.data)
        setPhotos(mediaRes.data.filter((m) => m.media_type === 'photo'))
      } catch (err) {
        setError(err.response?.data?.detail || 'Мемориал не найден')
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [id])

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
      alert('Ошибка при загрузке QR-кода')
    }
  }

  if (loading) return <div className="loading">Загрузка...</div>
  if (error || !memorial) return <div className="error-message">{error || 'Мемориал не найден'}</div>

  const birthYear = memorial.birth_date ? new Date(memorial.birth_date).getFullYear() : null
  const deathYear = memorial.death_date ? new Date(memorial.death_date).getFullYear() : null

  return (
    <div className="memorial-public">
      <div className="public-hero">
        {memorial.cover_photo_id && (
          <div className="public-cover-photo">
            <img
              src={getMediaUrl(memorial.cover_photo_id, 'medium')}
              alt={memorial.name}
              className="public-cover-img"
            />
          </div>
        )}
        <h1 className="public-name">{memorial.name}</h1>
        {(birthYear || deathYear) && (
          <p className="public-years">
            {birthYear && <span>{birthYear}</span>}
            {birthYear && deathYear && <span className="years-dash"> — </span>}
            {deathYear && <span>{deathYear}</span>}
          </p>
        )}
        {memorial.description && (
          <p className="public-description">{memorial.description}</p>
        )}
        <button className="btn btn-secondary" onClick={handleDownloadQR}>
          Скачать QR-код
        </button>
      </div>

      <nav className="public-nav">
        <button
          className={activeSection === 'chat' ? 'active' : ''}
          onClick={() => setActiveSection('chat')}
        >
          Поговорить с аватаром
        </button>
        <button
          className={activeSection === 'memories' ? 'active' : ''}
          onClick={() => setActiveSection('memories')}
        >
          Воспоминания {memories.length > 0 && `(${memories.length})`}
        </button>
        {photos.length > 0 && (
          <button
            className={activeSection === 'photos' ? 'active' : ''}
            onClick={() => setActiveSection('photos')}
          >
            Фотографии ({photos.length})
          </button>
        )}
      </nav>

      <div className="public-content">
        {activeSection === 'chat' && <AvatarChat memorialId={id} />}

        {activeSection === 'memories' && (
          <div className="public-memories">
            {memories.length === 0 ? (
              <p className="empty-state">Воспоминания не добавлены</p>
            ) : (
              memories.map((m) => (
                <div key={m.id} className="memory-card">
                  {m.title && <h3>{m.title}</h3>}
                  <p>{m.content}</p>
                  {m.event_date && (
                    <span className="event-date">
                      {new Date(m.event_date).toLocaleDateString('ru-RU', {
                        year: 'numeric',
                        month: 'long',
                      })}
                    </span>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {activeSection === 'photos' && (
          <div className="public-photos">
            {photos.map((p) => (
              <div key={p.id} className="public-photo-item">
                <img src={getMediaUrl(p.id)} alt={p.file_name} />
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="public-footer">
        <Link to={`/memorials/${id}`} className="manage-link">
          Управление мемориалом
        </Link>
      </div>
    </div>
  )
}

export default MemorialPublic
