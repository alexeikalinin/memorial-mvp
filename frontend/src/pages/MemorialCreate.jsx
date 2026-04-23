import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { memorialsAPI } from '../api/client'
import { useLanguage } from '../contexts/LanguageContext'
import { normalizeFlexibleDateInput, parseDateFieldForSubmit } from '../utils/dateInput'
import './MemorialCreate.css'

function MemorialCreate() {
  const navigate = useNavigate()
  const { t, lang } = useLanguage()
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    birth_date: '',
    death_date: '',
    is_public: false,
    voice_gender: '',
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

  const handleDateBlur = (field) => (e) => {
    const v = e.target.value.trim()
    if (!v) return
    const n = normalizeFlexibleDateInput(v)
    if (n && n !== e.target.value) {
      setFormData((prev) => ({ ...prev, [field]: n }))
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    const br = parseDateFieldForSubmit(formData.birth_date)
    const dr = parseDateFieldForSubmit(formData.death_date)
    if (!br.ok || !dr.ok) {
      setError(t('detail.date_invalid'))
      setLoading(false)
      return
    }

    try {
      const submitData = {
        ...formData,
        language: lang,
        birth_date: br.iso ? `${br.iso}T00:00:00Z` : null,
        death_date: dr.iso ? `${dr.iso}T00:00:00Z` : null,
        voice_gender: formData.voice_gender || null,
      }

      const response = await memorialsAPI.create(submitData)
      navigate(`/memorials/${response.data.id}`)
    } catch (err) {
      const errorData = err.response?.data
      if (errorData?.detail) {
        if (Array.isArray(errorData.detail)) {
          const errorMessages = errorData.detail.map((e) => {
            const field = e.loc?.join('.') || t('detail.validation_field')
            return `${field}: ${e.msg}`
          })
          setError(errorMessages.join('\n'))
        } else {
          setError(errorData.detail)
        }
      } else {
        setError(t('memorialCreate.error_create'))
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="memorial-create">
      <div className="memorial-create-card">
        <div className="memorial-create-header">
          <div className="create-icon">🕯</div>
          <h1>{t('memorialCreate.title')}</h1>
          <p>{t('memorialCreate.subtitle')}</p>
        </div>
        <form
          onSubmit={handleSubmit}
          className="memorial-form"
          lang={lang === 'en' ? 'en' : 'ru'}
        >
          {error && (
            <div className="error-message">
              {typeof error === 'string' ? (
                <pre style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{error}</pre>
              ) : (
                t('memorialCreate.error_create')
              )}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="name">{t('detail.label_name')}</label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
              placeholder={t('memorialCreate.name_placeholder')}
            />
          </div>

          <div className="form-group">
            <label htmlFor="description">{t('detail.label_description')}</label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleChange}
              rows="4"
              placeholder={t('memorialCreate.description_placeholder')}
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="birth_date">{t('detail.label_birth')}</label>
              <input
                type="text"
                id="birth_date"
                name="birth_date"
                value={formData.birth_date}
                onChange={handleChange}
                onBlur={handleDateBlur('birth_date')}
                placeholder={t('detail.date_placeholder')}
                autoComplete="off"
                inputMode="text"
                spellCheck={false}
              />
            </div>

            <div className="form-group">
              <label htmlFor="death_date">{t('detail.label_death')}</label>
              <input
                type="text"
                id="death_date"
                name="death_date"
                value={formData.death_date}
                onChange={handleChange}
                onBlur={handleDateBlur('death_date')}
                placeholder={t('detail.date_placeholder')}
                autoComplete="off"
                inputMode="text"
                spellCheck={false}
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="voice_gender">{t('memorialCreate.voice_label')}</label>
            <select
              id="voice_gender"
              name="voice_gender"
              value={formData.voice_gender}
              onChange={handleChange}
            >
              <option value="">{t('memorialCreate.voice_unspecified')}</option>
              <option value="male">{t('detail.voice_male')}</option>
              <option value="female">{t('detail.voice_female')}</option>
            </select>
            <span className="form-hint">{t('memorialCreate.voice_hint')}</span>
          </div>

          <div className="form-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                name="is_public"
                checked={formData.is_public}
                onChange={handleChange}
              />
              {t('detail.public_memorial')}
            </label>
          </div>

          <div className="form-actions">
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? t('memorialCreate.creating') : t('memorialCreate.submit')}
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => navigate('/')}
            >
              {t('detail.cancel')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default MemorialCreate
