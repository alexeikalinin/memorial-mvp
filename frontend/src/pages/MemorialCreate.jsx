import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { memorialsAPI } from '../api/client'
import './MemorialCreate.css'

function MemorialCreate() {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    birth_date: '',
    death_date: '',
    is_public: false,
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      // Преобразуем данные для отправки
      const submitData = {
        ...formData,
        // Преобразуем даты в ISO формат или null
        birth_date: formData.birth_date ? `${formData.birth_date}T00:00:00Z` : null,
        death_date: formData.death_date ? `${formData.death_date}T00:00:00Z` : null,
      }
      
      const response = await memorialsAPI.create(submitData)
      navigate(`/memorials/${response.data.id}`)
    } catch (err) {
      // Обработка ошибок валидации
      const errorData = err.response?.data
      if (errorData?.detail) {
        // Если detail - массив (ошибки валидации), форматируем их
        if (Array.isArray(errorData.detail)) {
          const errorMessages = errorData.detail.map((err) => {
            const field = err.loc?.join('.') || 'поле'
            return `${field}: ${err.msg}`
          })
          setError(errorMessages.join('\n'))
        } else {
          // Если detail - строка
          setError(errorData.detail)
        }
      } else {
        setError('Ошибка при создании мемориала')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="memorial-create">
      <h1>Создать мемориал</h1>
      <form onSubmit={handleSubmit} className="memorial-form">
        {error && (
          <div className="error-message">
            {typeof error === 'string' ? (
              <pre style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{error}</pre>
            ) : (
              'Ошибка при создании мемориала'
            )}
          </div>
        )}

        <div className="form-group">
          <label htmlFor="name">Имя *</label>
          <input
            type="text"
            id="name"
            name="name"
            value={formData.name}
            onChange={handleChange}
            required
            placeholder="Имя человека"
          />
        </div>

        <div className="form-group">
          <label htmlFor="description">Описание</label>
          <textarea
            id="description"
            name="description"
            value={formData.description}
            onChange={handleChange}
            rows="4"
            placeholder="Краткое описание или биография"
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="birth_date">Дата рождения</label>
            <input
              type="date"
              id="birth_date"
              name="birth_date"
              value={formData.birth_date}
              onChange={handleChange}
            />
          </div>

          <div className="form-group">
            <label htmlFor="death_date">Дата смерти</label>
            <input
              type="date"
              id="death_date"
              name="death_date"
              value={formData.death_date}
              onChange={handleChange}
            />
          </div>
        </div>

        <div className="form-group">
          <label className="checkbox-label">
            <input
              type="checkbox"
              name="is_public"
              checked={formData.is_public}
              onChange={handleChange}
            />
            Публичный мемориал
          </label>
        </div>

        <div className="form-actions">
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Создание...' : 'Создать мемориал'}
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => navigate('/')}
          >
            Отмена
          </button>
        </div>
      </form>
    </div>
  )
}

export default MemorialCreate

