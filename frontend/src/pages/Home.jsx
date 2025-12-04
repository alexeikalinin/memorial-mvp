import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import './Home.css'

function Home() {
  const [memorials, setMemorials] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // TODO: Загрузить список мемориалов
    // Пока заглушка
    setLoading(false)
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
                <h3>{memorial.name}</h3>
                <p>{memorial.description}</p>
              </Link>
            ))
          )}
        </div>
      )}
    </div>
  )
}

export default Home

