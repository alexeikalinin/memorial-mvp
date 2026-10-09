import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useNavigate } from 'react-router-dom'
import { memorialsAPI, familyAPI } from '../api/client'
import { useLanguage } from '../contexts/LanguageContext'
import {
  parseDateFieldForSubmit,
  formatDateWithDots,
  dateCursorPosition,
} from '../utils/dateInput'
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
  const [savedPage, setSavedPage] = useState(null)
  const [linkEnabled, setLinkEnabled] = useState(false)
  const [relativeQuery, setRelativeQuery] = useState('')
  const [relatives, setRelatives] = useState([])
  const [relative, setRelative] = useState(null)
  const [relationshipType, setRelationshipType] = useState('spouse')
  const [linkPublic, setLinkPublic] = useState(false)
  const [similarPages, setSimilarPages] = useState([])
  const [searchError, setSearchError] = useState('')
  const [living, setLiving] = useState(false)
  const [livingConsent, setLivingConsent] = useState(false)
  useEffect(() => {
    let active = true
    if (formData.name.trim().length < 3 || savedPage) { setSimilarPages([]); return }
    const timer = setTimeout(() => familyAPI.searchMemorials(formData.name.trim()).then(res => {
      if (active) setSimilarPages(res.data)
    }).catch(() => { if (active) setSimilarPages([]) }), 350)
    return () => { active = false; clearTimeout(timer) }
  }, [formData.name, savedPage])
  useEffect(() => {
    let active = true
    if (!linkEnabled) return
    const timer = setTimeout(() => familyAPI.searchMemorials(relativeQuery.trim()).then(res => {
      if (active) { setRelatives(res.data.filter(m => m.id !== savedPage?.id)); setSearchError('') }
    }).catch(() => { if (active) setSearchError(lang === 'ru' ? 'Не удалось загрузить родственников.' : 'Could not load relatives.') }), 250)
    return () => { active = false; clearTimeout(timer) }
  }, [linkEnabled, relativeQuery, savedPage?.id, lang])

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }))
  }

  const handleDateInput = (field) => (e) => {
    const el = e.target
    const cursorBefore = el.selectionStart ?? el.value.length
    const digitsBeforeCursor = el.value.slice(0, cursorBefore).replace(/\D/g, '').length
    const formatted = formatDateWithDots(el.value)
    const newCursor = Math.min(dateCursorPosition(digitsBeforeCursor), formatted.length)
    el.value = formatted
    el.setSelectionRange(newCursor, newCursor)
    setFormData((prev) => ({ ...prev, [field]: formatted }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    const br = parseDateFieldForSubmit(formData.birth_date)
    const dr = parseDateFieldForSubmit(living ? '' : formData.death_date)
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

      const page = savedPage || (await memorialsAPI.create(submitData)).data
      setSavedPage(page)
      if (linkEnabled && relative) {
        const response = await familyAPI.createRelationship(page.id, { related_memorial_id: relative.id, relationship_type: relationshipType, is_public: linkPublic })
        navigate(`/memorials/${page.id}?tab=family`, { state: { justCreated: true, familyRequestPending: response.data?.status === 'pending' } })
      } else navigate(`/memorials/${page.id}`, { state: { justCreated: true } })
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

          <fieldset disabled={!!savedPage} style={{ border: 0, margin: 0, padding: 0 }}>
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
            <label htmlFor="voice_gender">{t('memorialCreate.gender_label')}</label>
            <select
              id="voice_gender"
              name="voice_gender"
              value={formData.voice_gender}
              onChange={handleChange}
              required
            >
              <option value="" disabled>{t('memorialCreate.gender_placeholder')}</option>
              <option value="male">{t('detail.voice_male')}</option>
              <option value="female">{t('detail.voice_female')}</option>
            </select>
            <span className="form-hint">{t('memorialCreate.gender_hint')}</span>
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
                onChange={handleDateInput('birth_date')}
                placeholder={t('memorialCreate.date_placeholder')}
                autoComplete="off"
                inputMode="numeric"
                maxLength={10}
                spellCheck={false}
              />
            </div>

            <div className="form-group">
              <label htmlFor="death_date">{t('detail.label_death')}</label>
              <input
                type="text"
                id="death_date"
                disabled={living}
                name="death_date"
                value={formData.death_date}
                onChange={handleDateInput('death_date')}
                placeholder={t('memorialCreate.date_placeholder')}
                autoComplete="off"
                inputMode="numeric"
                maxLength={10}
                spellCheck={false}
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
              <span>{t('detail.public_memorial')}</span>
              <span
                className="info-trigger"
                tabIndex={0}
                title={t('memorialCreate.public_memorial_hint')}
                onClick={(e) => e.preventDefault()}
              >?</span>
              <span className="info-tooltip">{t('memorialCreate.public_memorial_hint')}</span>
            </label>
          </div>

          <label className="checkbox-label"><input type="checkbox" checked={living} onChange={e => setLiving(e.target.checked)} /><span>{lang === 'ru' ? 'Человек жив' : 'This person is living'}</span></label>
          {living && <label className="checkbox-label"><input type="checkbox" required checked={livingConsent} onChange={e => setLivingConsent(e.target.checked)} /><span>{lang === 'ru' ? 'У меня есть согласие этого человека на создание его страницы.' : 'I have this person’s consent to create their page.'}</span></label>}
          </fieldset>
          {similarPages.length > 0 && <section className="form-group"><p>{lang === 'ru' ? 'Найдены похожие страницы. Проверьте, нет ли уже мемориала этого человека:' : 'Similar pages found. Check whether this person already has a memorial:'}</p>{similarPages.map(m => <p key={m.id}><Link to={`/${m.is_public === false ? 'memorials' : 'm'}/${m.id}`} target="_blank" rel="noopener noreferrer">{m.name} {m.birth_date ? new Date(m.birth_date).getFullYear() : ''}{m.death_date ? ` — ${new Date(m.death_date).getFullYear()}` : ''}</Link></p>)}</section>}
          {savedPage && <p role="status">{lang === 'ru' ? 'Страница уже создана. Повторите только сохранение связи или добавьте её позже.' : 'The page has been created. Retry the relationship or add it later.'} <Link to={`/memorials/${savedPage.id}?tab=family`}>{lang === 'ru' ? 'Открыть дерево' : 'Open tree'}</Link></p>}
          <div className="form-group"><label className="checkbox-label"><input type="checkbox" checked={linkEnabled} disabled={loading} onChange={e => setLinkEnabled(e.target.checked)} /><span>{lang === 'ru' ? 'Связать с родственником сейчас (необязательно)' : 'Link a relative now (optional)'}</span></label></div>
          {linkEnabled && <section className="form-group">
            <label htmlFor="create-relative-search">{lang === 'ru' ? 'Найти существующий мемориал родственника' : 'Find an existing relative memorial'}</label>
            <input id="create-relative-search" value={relativeQuery} disabled={loading} onChange={e => { setRelativeQuery(e.target.value); setRelative(null); setRelatives([]) }} />
            {searchError && <p role="alert">{searchError}</p>}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>{relatives.map(m => <button className="btn" type="button" disabled={loading} aria-pressed={relative?.id === m.id} key={m.id} onClick={() => setRelative(m)}>{m.name} {m.birth_date ? new Date(m.birth_date).getFullYear() : ''}</button>)}</div>
            <label htmlFor="create-relation">{lang === 'ru' ? 'Этот родственник приходится создаваемому человеку' : 'This relative is related to the new person as'}</label>
            <select id="create-relation" value={relationshipType} disabled={loading} onChange={e => setRelationshipType(e.target.value)}>{[['parent','Родитель','Parent'],['child','Ребёнок','Child'],['spouse','Супруг / супруга','Spouse'],['sibling','Брат / сестра','Sibling'],['ex_spouse','Бывший супруг / супруга','Former spouse'],['half_sibling','Неполнородный брат / сестра','Half-sibling'],['partner','Партнёр','Partner'],['adoptive_parent','Приёмный родитель','Adoptive parent'],['adoptive_child','Приёмный ребёнок','Adoptive child'],['step_parent','Отчим / мачеха','Stepparent'],['step_child','Пасынок / падчерица','Stepchild']].map(([value,ru,en]) => <option key={value} value={value}>{lang === 'ru' ? ru : en}</option>)}</select>
            {relative && <p>{relative.name} — {({ parent: lang === 'ru' ? 'родитель' : 'parent', child: lang === 'ru' ? 'ребёнок' : 'child', spouse: lang === 'ru' ? 'супруг / супруга' : 'spouse', sibling: lang === 'ru' ? 'брат / сестра' : 'sibling', ex_spouse: lang === 'ru' ? 'бывший супруг / супруга' : 'former spouse', half_sibling: lang === 'ru' ? 'неполнородный брат / сестра' : 'half-sibling', partner: lang === 'ru' ? 'партнёр' : 'partner', adoptive_parent: lang === 'ru' ? 'приёмный родитель' : 'adoptive parent', adoptive_child: lang === 'ru' ? 'приёмный ребёнок' : 'adoptive child', step_parent: lang === 'ru' ? 'отчим / мачеха' : 'stepparent', step_child: lang === 'ru' ? 'пасынок / падчерица' : 'stepchild' })[relationshipType]} {lang === 'ru' ? 'для' : 'of'} {formData.name}.</p>}
            <label className="checkbox-label"><input type="checkbox" checked={linkPublic} disabled={loading} onChange={e => setLinkPublic(e.target.checked)} /><span>{lang === 'ru' ? 'Показывать связь публично' : 'Show relationship publicly'}</span></label>
            <p className="form-hint">{lang === 'ru' ? 'Другой владелец должен подтвердить связь. Это не выдаёт права редактирования. Можно пропустить этот шаг.' : 'A different owner must approve the link. It does not grant editing rights. You can skip this step.'}</p>
          </section>}
          <div className="form-actions">
            <button type="submit" className="btn btn-primary" disabled={loading || (linkEnabled && !relative)}>
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
