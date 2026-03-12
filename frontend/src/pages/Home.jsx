import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { memorialsAPI, getMediaUrl } from '../api/client'
import './Home.css'

function Home() {
  const [memorials, setMemorials] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    memorialsAPI.list()
      .then((res) => setMemorials(Array.isArray(res.data) ? res.data : []))
      .catch((err) => {
        console.error('Error loading memorials:', err)
        setMemorials([])
      })
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="home">
      <div className="hero">
        <div className="hero-inner">
          <div className="hero-text">
            <span className="hero-label">Виртуальный мемориал</span>
            <h1 className="hero-tagline">
              Мы сохраняем личность человека,<br/>
              а не просто фотографии
            </h1>
            <p className="hero-subtitle">
              Создайте цифровую память о близких людях — с голосом, воспоминаниями и семейным деревом
            </p>
            <Link to="/memorials/new" className="btn btn-memorial">
              Создать мемориал
            </Link>
          </div>
          <div className="hero-visual" aria-hidden="true">
            <svg width="120" height="200" viewBox="0 0 120 200" fill="none" xmlns="http://www.w3.org/2000/svg">
              <defs>
                <linearGradient id="candleGrad" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="#c8a97e"/>
                  <stop offset="40%" stopColor="#f0ddb8"/>
                  <stop offset="100%" stopColor="#a07850"/>
                </linearGradient>
                <radialGradient id="glowGrad" cx="50%" cy="60%" r="50%">
                  <stop offset="0%" stopColor="#fbbf24" stopOpacity="0.35"/>
                  <stop offset="100%" stopColor="#f59e0b" stopOpacity="0"/>
                </radialGradient>
              </defs>
              {/* Ореол */}
              <ellipse className="candle-glow" cx="60" cy="95" rx="52" ry="68" fill="url(#glowGrad)"/>
              {/* Пламя */}
              <g className="candle-flame">
                <path d="M60 42 C54 55 50 65 52 75 C54 83 58 87 60 88 C62 87 66 83 68 75 C70 65 66 55 60 42Z" fill="#fde68a"/>
                <path d="M60 52 C57 61 55 68 57 75 C58 80 60 83 60 84 C60 83 62 80 63 75 C65 68 63 61 60 52Z" fill="#fbbf24"/>
                <path d="M60 62 C58 67 58 72 59 76 C59.5 79 60 81 60 82 C60 81 60.5 79 61 76 C62 72 62 67 60 62Z" fill="#f97316"/>
              </g>
              {/* Тело свечи */}
              <rect x="42" y="88" width="36" height="90" rx="3" fill="url(#candleGrad)"/>
              {/* Блик на свече */}
              <rect x="48" y="92" width="6" height="82" rx="3" fill="white" opacity="0.18"/>
              {/* Фитиль */}
              <line x1="60" y1="88" x2="60" y2="94" stroke="#4b3a2a" strokeWidth="1.5"/>
              {/* Воск */}
              <ellipse cx="60" cy="88" rx="18" ry="4" fill="#e8d5b0"/>
              {/* Подставка */}
              <rect x="35" y="178" width="50" height="8" rx="4" fill="#8b6840"/>
              <rect x="30" y="184" width="60" height="6" rx="3" fill="#6b4f30"/>
            </svg>
          </div>
        </div>
      </div>

      <div className="home-content">
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
                      src={getMediaUrl(memorial.cover_photo_id, 'small')}
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
    </div>
  )
}

export default Home

