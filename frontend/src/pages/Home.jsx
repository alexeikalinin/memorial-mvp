import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { memorialsAPI } from '../api/client'
import './Home.css'

function Home() {
  const [memorials, setMemorials] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    memorialsAPI.list()
      .then((res) => setMemorials(res.data))
      .catch((err) => console.error('Error loading memorials:', err))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="home">
      <div className="hero">
        <h1>Виртуальный мемориал</h1>
        <p>Создайте цифровую память о близких людях</p>
        <Link to="/memorials/new" className="btn btn-primary">
          Создать мемориал
        </Link>
      </div>

      {loading ? (
        <div className="loading">Загрузка...</div>
      ) : (
        <div className="memorials-grid">
          {memorials.length === 0 ? (
            <div className="empty-state">
              <p>Пока нет созданных мемориалов</p>
              <Link to="/memorials/new" className="btn btn-primary">
                Создать первый мемориал
              </Link>
            </div>
          ) : (
            memorials.map((memorial) => (
              <Link
                key={memorial.id}
                to={`/memorials/${memorial.id}`}
                className="memorial-card"
              >
                {memorial.cover_photo_id && (
                  <div className="card-cover">
                    <img
                      src={`/api/v1/media/${memorial.cover_photo_id}?thumbnail=small`}
                      alt={memorial.name}
                      className="card-cover-img"
                    />
                  </div>
                )}
                <h3>{memorial.name}</h3>
                {memorial.description && <p className="card-description">{memorial.description}</p>}
                <div className="card-meta">
                  {(memorial.birth_date || memorial.death_date) && (
                    <span className="card-dates">
                      {memorial.birth_date && new Date(memorial.birth_date).getFullYear()}
                      {memorial.birth_date && memorial.death_date && ' — '}
                      {memorial.death_date && new Date(memorial.death_date).getFullYear()}
                    </span>
                  )}
                  <span className="card-counts">
                    {memorial.memories_count} воспоминаний · {memorial.media_count} файлов
                  </span>
                </div>
              </Link>
            ))
          )}
        </div>
      )}
    </div>
  )
}

export default Home

