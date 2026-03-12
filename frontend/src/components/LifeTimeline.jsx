import { useState, useEffect } from 'react'
import { memorialsAPI } from '../api/client'
import './LifeTimeline.css'

function LifeTimeline({ memorialId }) {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    memorialsAPI.getTimeline(memorialId)
      .then((res) => setItems(Array.isArray(res.data) ? res.data : []))
      .catch((err) => {
        console.error('Error loading timeline:', err)
        setItems([])
      })
      .finally(() => setLoading(false))
  }, [memorialId])

  if (loading) return <div className="loading">Загрузка хронологии...</div>

  if (items.length === 0) {
    return (
      <div className="timeline-empty">
        <p>Нет воспоминаний с датой события</p>
        <p className="hint">
          Добавьте дату «Когда это было» к воспоминаниям, чтобы они появились здесь
        </p>
      </div>
    )
  }

  let lastYear = null

  return (
    <div className="life-timeline">
      <h2 className="timeline-title">Хронология жизни</h2>
      <div className="timeline-line-container">
        {items.map((item) => {
          const showYear = item.year !== lastYear
          lastYear = item.year
          return (
            <div key={item.id}>
              {showYear && (
                <div className="timeline-year-label">{item.year}</div>
              )}
              <div className="timeline-entry">
                <div className="timeline-dot" />
                <div className="timeline-card">
                  <span className="timeline-date">{item.date_label}</span>
                  {item.title && <h3 className="timeline-card-title">{item.title}</h3>}
                  <p className="timeline-card-content">
                    {item.content.length > 200
                      ? item.content.slice(0, 200) + '…'
                      : item.content}
                  </p>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default LifeTimeline
