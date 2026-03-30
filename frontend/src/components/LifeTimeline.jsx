import { useState, useEffect } from 'react'
import { memorialsAPI } from '../api/client'
import { useLanguage } from '../contexts/LanguageContext'
import './LifeTimeline.css'

function formatEventLabel(iso, lang) {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  const locale = lang === 'ru' ? 'ru-RU' : 'en-US'
  return d.toLocaleDateString(locale, { month: 'long', year: 'numeric' })
}

function LifeTimeline({ memorialId }) {
  const { t, lang } = useLanguage()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    memorialsAPI
      .getTimeline(memorialId)
      .then((res) => setItems(Array.isArray(res.data) ? res.data : []))
      .catch((err) => {
        console.error('Error loading timeline:', err)
        setItems([])
      })
      .finally(() => setLoading(false))
  }, [memorialId])

  if (loading) {
    return <div className="loading">{t('lifeTimeline.loading')}</div>
  }

  if (items.length === 0) {
    return (
      <div className="timeline-empty">
        <p>{t('lifeTimeline.empty_title')}</p>
        <p className="hint">{t('lifeTimeline.empty_hint')}</p>
      </div>
    )
  }

  let lastYear = null

  return (
    <div className="life-timeline">
      <h2 className="timeline-title">{t('lifeTimeline.title')}</h2>
      <div className="timeline-line-container">
        {items.map((item) => {
          const showYear = item.year !== lastYear
          lastYear = item.year
          const dateLabel =
            item.event_date != null
              ? formatEventLabel(item.event_date, lang)
              : item.date_label
          return (
            <div key={item.id}>
              {showYear && (
                <div className="timeline-year-label">{item.year}</div>
              )}
              <div className="timeline-entry">
                <div className="timeline-dot" />
                <div className="timeline-card">
                  <span className="timeline-date">{dateLabel}</span>
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
