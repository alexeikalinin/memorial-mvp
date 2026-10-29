import {GUEST_ANSWERS_ENABLED} from '../config/guestAnswers'
import {Link,useLocation} from 'react-router-dom'
import { useEffect, useState } from 'react'
import apiClient from '../api/client'
import ChatAudioPlayer from './ChatAudioPlayer'
import { useLanguage } from '../contexts/LanguageContext'
import './FeaturedAnswers.css'

function FeaturedAnswersContent({ memorialId, owner = false, inviteToken, question, onLoaded, memoryId }) {
  const { lang } = useLanguage()
  const location=useLocation()
  const routeKey=`${location.pathname}${location.search}`
  const en = lang === 'en'
  const [rows, setRows] = useState([])
  const [open, setOpen] = useState(Boolean(memoryId))
  const [showStale, setShowStale] = useState(false)
  const [expanded, setExpanded] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [selected, setSelected] = useState(null)
  const [preview, setPreview] = useState(null)
  const revoice = async row => {
    setBusy(true); setError('')
    try {
      const { data } = await apiClient.post('/ai/avatar/chat', { ...(row.audio_variants.find(v => v.key === row.audio_variant)?.generation_settings || row.generation_settings), memorial_id: memorialId, question: row.question, include_audio: true, regenerate_audio: true, include_family_memories: false })
      if (!data.audio_url || !data.audio_preview_id) throw new Error(data.audio_error || (en ? 'Could not create audio' : 'Не удалось создать дубль'))
      setPreview({ cacheId: data.answer_cache_id, id: data.audio_preview_id, url: data.audio_url })
    } catch (e) { setError(e.response?.data?.detail || e.message) }
    finally { setBusy(false) }
  }
  const choose = async accept => {
    setBusy(true)
    try { await apiClient.post(`/ai/avatar/audio-preview/${preview.cacheId}/${preview.id}`, { accept }); setPreview(null); await load() }
    catch (e) { setError(e.response?.data?.detail || e.message) }
    finally { setBusy(false) }
  }
  const load = async () => {
    setError('')
    try {
      const result = await apiClient.get(`/featured-answers/memorials/${memorialId}/${owner ? 'saved' : 'guest'}`, { params: owner ? {} : { invite_token: inviteToken } })
      setRows(result.data); onLoaded?.(result.data)
    } catch (e) { setError(e.response?.data?.detail || (en ? 'Could not load saved answers' : 'Не удалось загрузить сохранённые ответы')) }
  }
  useEffect(() => {
    let active = true
    setRows([]); setSelected(null); setError('')
    if (!question) apiClient.get(`/featured-answers/memorials/${memorialId}/${owner ? 'saved' : 'guest'}`, { params: owner ? {} : { invite_token: inviteToken } })
      .then(r => { if (active) { setRows(r.data); onLoaded?.(r.data) } })
      .catch(e => { if (active && owner) setError(e.response?.data?.detail || (en ? 'Could not load saved answers' : 'Не удалось загрузить сохранённые ответы')) })
    return () => { active = false }
  }, [memorialId, owner, inviteToken, question, en, onLoaded, routeKey])
  const update = async (row, publish, variant = row.audio_variant, position = row.position ?? rows.filter(r => r.featured).length) => {
    setBusy(true); setError('')
    try {
      await apiClient.put(`/featured-answers/saved/${row.cache_id}`, { publish_to_guests: publish, audio_variant: variant || null, position: Math.min(position, 4) })
      await load()
    } catch (e) { setError(e.response?.data?.detail || (en ? 'Could not save' : 'Не удалось сохранить')) }
    finally { setBusy(false) }
  }
  const playable = value => {
    if (!value) return null
    const base = (import.meta.env.VITE_API_URL || '/api/v1').replace(/\/$/, '')
    return value.startsWith('/api/v1/') ? `${base}${value.slice(7)}` : value
  }
  if (!owner) return rows.length > 0 && <section className="featured-answers" aria-label={en ? 'Meet the avatar' : 'Знакомство с аватаром'}>
    <h3>{en ? 'Meet the avatar' : 'Знакомство с аватаром'}</h3>
    <p>{en ? 'Answers chosen by the family. No new generation.' : 'Готовые ответы, выбранные семьёй. Не расходуют пять свободных вопросов.'}</p>
    <div className="featured-questions">{rows.map(row => <button type="button" key={row.id} aria-pressed={selected === row.id} onClick={() => setSelected(row.id)}>{row.question}</button>)}</div>
    {rows.filter(row => row.id === selected).map(row => <article key={row.id}><p className="featured-answer-text">{row.answer}</p>{row.audio_url && <ChatAudioPlayer src={playable(row.audio_url)} />}</article>)}
  </section>
  const visible = rows.filter(row => (!memoryId || (row.source_memory_ids.includes(memoryId) && row.audio_variants.length > 0)) && (!question || row.question.trim().toLowerCase() === question.trim().toLowerCase()) && (showStale || !row.stale || row.featured))
  return <details className="featured-answers" open={open} onToggle={e => { if (e.target !== e.currentTarget) return; setOpen(e.currentTarget.open); if (e.currentTarget.open) load() }}>
    <summary>{memoryId ? (en ? 'Saved audio answers' : 'Озвученные ответы') : (en ? 'Answers and audio' : 'Ответы и озвучка')}{!memoryId && ` · ${en ? 'For guests' : 'Для гостей'} ${rows.filter(r => r.featured).length}/5`}</summary>
    <p>{en ? 'Selected text and audio will be accessible to visitors and chat invite holders. Check that they contain no private family information.' : 'Выбранные текст и аудио будут доступны посетителям публичной страницы и приглашённым с доступом к чату. Проверьте, что в них нет закрытых семейных сведений.'}</p>
    {!memoryId && <><p>{en?'0/5 means the number of selected guest answers, not a question limit. Up to five prepared answers can be selected.':'0/5 — число выбранных ответов для гостей, а не лимит вопросов. Можно выбрать до пяти готовых ответов.'}</p><ol><li>{en?'Open guest preparation, ask a question, and enable Voice before sending if you want audio.':'Откройте подготовку, задайте вопрос; для озвучки включите «Голос» перед отправкой.'}</li><li>{en?'Return here, expand the saved question and enable “Show to guests”.':'Вернитесь сюда, раскройте сохранённый вопрос и включите «Предлагать гостям».'}</li><li>{en?'Listen to the takes, choose the guest audio and its position. Selecting existing text/audio does not generate new content.':'Прослушайте записи, выберите озвучку и позицию. Выбор уже готового текста и аудио не запускает новую генерацию.'}</li></ol><Link className="btn btn-secondary" to={`/memorials/${memorialId}?tab=chat&prepareGuests=1`}>{en?'Prepare an answer for guests':'Подготовить ответ для гостей'}</Link><p>{en?'Family-context conversations and old browser chat history do not appear here. Only saved answers based on this memorial are eligible.':'Разговоры с воспоминаниями родственников и старая переписка из истории браузера сюда не попадают. Здесь выбираются сохранённые ответы на основе этого мемориала.'}</p></>}
    {error && <p role="alert">{String(error)}</p>}
    {!visible.length && <p>{en ? 'No saved answers yet. Use “Prepare an answer for guests” above.' : 'Сохранённых ответов пока нет. Нажмите «Подготовить ответ для гостей» выше.'}</p>}
    {rows.some(row => row.stale && !row.featured) && <label><input type="checkbox" checked={showStale} onChange={e => setShowStale(e.target.checked)} /> {en ? 'Show outdated answers' : 'Показать устаревшие ответы'}</label>}
    {visible.map(row => <article className="featured-saved-row" key={row.cache_id} data-cache-id={row.cache_id}>
      <button type="button" className="btn btn-secondary" aria-expanded={!!question || expanded === row.cache_id} onClick={() => setExpanded(expanded === row.cache_id ? null : row.cache_id)}>{row.question} · {row.featured ? (en ? 'Selected' : 'Выбран') : row.audio_variants.length ? (en ? 'Audio saved' : 'Есть озвучка') : (en ? 'Text' : 'Текст')}</button>
      {(question || expanded === row.cache_id) && <><p className="featured-answer-text">{row.answer}</p>
      <p>{row.stale ? (en ? 'Needs review: ask again' : 'Нужно проверить: задайте вопрос снова') : row.audio_variants.length ? (en ? 'Audio saved' : 'Озвучка сохранена') : (en ? 'Text only' : 'Только текст')}</p>
      {row.sources.length > 0 && <details><summary>{en ? 'Sources' : 'Воспоминания — источники'}</summary><ul>{row.sources.map((s, i) => <li key={i}>{s}</li>)}</ul></details>}
      <label><input type="checkbox" checked={row.featured} disabled={busy || (row.stale && !row.featured)} onChange={e => update(row, e.target.checked, row.audio_variant || row.audio_variants[0]?.key)} /> {en ? 'Show to guests' : 'Предлагать гостям'}</label>
      {row.audio_variants.map((variant, i) => <div key={variant.key}><ChatAudioPlayer src={playable(variant.audio_url)} />{row.featured && <label><input type="radio" name={`featured-audio-${row.cache_id}`} checked={row.audio_variant === variant.key} disabled={busy || row.stale} onChange={() => update(row, true, variant.key)} />{en ? `Audio ${i + 1}` : `Озвучка ${i + 1}`}</label>}</div>)}
      {preview?.cacheId === row.cache_id && <section><p>{en ? 'New take. Previous audio stays active until you choose.' : 'Новый дубль. Прежняя запись активна до вашего выбора.'}</p><ChatAudioPlayer src={playable(preview.url)} /><button type="button" disabled={busy} onClick={() => choose(true)}>{en ? 'Use this take' : 'Использовать этот вариант'}</button><button type="button" disabled={busy} onClick={() => choose(false)}>{en ? 'Keep previous' : 'Оставить прежний'}</button></section>}
      <button type="button" disabled={busy || row.stale || !!preview} onClick={() => revoice(row)}>{en ? 'Create new audio take (paid)' : 'Создать новый дубль (платно)'}</button>
      {row.featured && <label>{en ? 'Position' : 'Позиция'} <select value={row.position ?? 0} disabled={busy || row.stale} onChange={e => update(row, true, row.audio_variant, Number(e.target.value))}>{[0, 1, 2, 3, 4].map(n => <option key={n} value={n}>{n + 1}</option>)}</select></label>}
    </>}</article>)}
  </details>
}

export default function FeaturedAnswers(props) {
  return GUEST_ANSWERS_ENABLED ? <FeaturedAnswersContent {...props}/> : null
}
