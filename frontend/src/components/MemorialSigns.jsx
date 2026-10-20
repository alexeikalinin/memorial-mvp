import { useEffect, useRef, useState } from 'react'
import apiClient from '../api/client'
import { getVisitorId } from '../utils/visitorIdentity'
import { FLOWER_TYPES, FLOWER_COLORS, CANDLE_TYPES, FlowerArtwork, MemorialCandle, signDescription } from './MemorialAppearance'
import './MemorialSigns.css'

export function MemorialSigns({ memorialId, lang, onChange }) {
  const [items, setItems] = useState([])
  const [choice, setChoice] = useState(null)
  const [name, setName] = useState('')
  const [comment, setComment] = useState('')
  const [flowerType, setFlowerType] = useState('carnations')
  const [flowerColor, setFlowerColor] = useState('red')
  const [candle, setCandle] = useState('classic')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [loadError, setLoadError] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const requestVersion = useRef(0)
  const picker = useRef(null)
  const ru = lang === 'ru'

  async function load() {
    const version = requestVersion.current
    try {
      const { data } = await apiClient.get(`/memorials/${memorialId}/signs`)
      if (version !== requestVersion.current) return
      setLoadError(''); setItems(data.items); onChange?.(data)
    } catch {
      if (version === requestVersion.current) setLoadError(ru ? 'Не удалось обновить знаки памяти.' : 'Could not refresh signs.')
    }
  }
  useEffect(() => {
    requestVersion.current++; setItems([]); setConfirmation(''); load()
    const timer = setInterval(load, 60000)
    return () => { requestVersion.current++; clearInterval(timer) }
  }, [memorialId])
  useEffect(() => {
    if (!choice) return
    const update = () => {
      const viewport = window.visualViewport
      picker.current?.style.setProperty('--signs-vp-height', `${viewport?.height || innerHeight}px`)
      picker.current?.style.setProperty('--signs-vp-center', `${(viewport?.offsetTop || 0) + (viewport?.height || innerHeight) / 2}px`)
    }
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    update()
    window.visualViewport?.addEventListener('resize', update)
    window.visualViewport?.addEventListener('scroll', update)
    window.addEventListener('resize', update)
    return () => {
      document.body.style.overflow = previousOverflow
      window.visualViewport?.removeEventListener('resize', update)
      window.visualViewport?.removeEventListener('scroll', update)
      window.removeEventListener('resize', update)
    }
  }, [choice])
  function close() { picker.current?.close(); setChoice(null) }
  function open(kind) { setChoice(kind); setError(''); setConfirmation(''); picker.current.showModal() }
  async function submit(event) {
    event.preventDefault()
    if (busy) return
    setBusy(true); setError('')
    try {
      const { data } = await apiClient.post(`/memorials/${memorialId}/signs`, {
        kind: choice, variant: choice === 'candle' ? candle : flowerType,
        ...(choice === 'flowers' ? { flower_type: flowerType, flower_color: flowerColor } : {}),
        display_name: name.trim(), comment: comment.trim(),
      }, { headers: { 'X-Memorial-Visitor': getVisitorId('memorialVisitor') } })
      const updatedItems = [data, ...items.filter(item => item.id !== data.id)]
      setItems(updatedItems)
      onChange?.({ items: updatedItems, candle_lit: updatedItems.some(item => item.kind === 'candle') })
      setConfirmation(data.already_active
        ? (ru ? 'Ваш знак памяти обновлён. Срок остаётся прежним — 24 часа с первого действия.' : 'Your sign has been updated. It still expires 24 hours after the first action.')
        : (choice === 'candle' ? (ru ? 'Свеча зажжена. Спасибо за вашу память.' : 'Your candle is lit. Thank you for remembering.') : (ru ? 'Цветы оставлены. Спасибо за вашу память.' : 'Your flowers have been placed. Thank you for remembering.')))
      close()
      await load()
    } catch (e) {
      setError(typeof e.response?.data?.detail === 'string' ? e.response.data.detail : (ru ? 'Не удалось оставить знак памяти. Попробуйте ещё раз.' : 'Could not leave a sign. Please retry.'))
    } finally { setBusy(false) }
  }
  const visibleItems = [...items.filter(item => item.kind === 'candle').slice(0, 3), ...items.filter(item => item.kind === 'flowers').slice(0, 3)]
  return <section className="memorial-signs">
    <div className="memorial-signs-actions">
      <button type="button" onClick={() => open('candle')}>{ru ? 'Зажечь свечу' : 'Light a candle'}</button>
      <button type="button" onClick={() => open('flowers')}>{ru ? 'Оставить цветы' : 'Leave flowers'}</button>
      <span>{ru ? 'На 24 часа' : 'For 24 hours'}</span>
    </div>
    {confirmation && <p role="status" className="signs-confirmation">{confirmation}</p>}
    {loadError && <p role="alert">{loadError} <button type="button" onClick={load}>{ru ? 'Повторить' : 'Retry'}</button></p>}
    <div className="memorial-visitor-signs" aria-label={ru ? 'Оставленные знаки памяти' : 'Signs of remembrance'}>
      {visibleItems.map(item => <button type="button" key={item.id} className={`visitor-sign visitor-${item.kind}`} title={signDescription(item, lang)} aria-label={signDescription(item, lang)}>
        {item.kind === 'flowers' ? <FlowerArtwork type={item.flower_type || 'carnations'} color={item.flower_color || 'red'} /> : <MemorialCandle variant={item.variant} />}
        <span className="visitor-tooltip">{signDescription(item, lang)}<br />{item.comment && <>{item.comment}<br /></>}{new Date(item.created_at).toLocaleString(ru ? 'ru-RU' : 'en-US')}<br />{ru ? 'До' : 'Until'} {new Date(item.expires_at).toLocaleString(ru ? 'ru-RU' : 'en-US')}</span>
      </button>)}
      {items.length > visibleItems.length && <span>+{items.length - visibleItems.length}</span>}
    </div>
    <dialog ref={picker} className="signs-dialog signs-picker" aria-labelledby="signs-title" onClose={() => setChoice(null)} onCancel={event => { if (busy) event.preventDefault(); else setChoice(null) }}>
      <form className="signs-form" onSubmit={submit}>
        <header className="signs-dialog-header"><h2 id="signs-title">{choice === 'candle' ? (ru ? 'Зажечь свечу' : 'Light a candle') : (ru ? 'Оставить цветы' : 'Leave flowers')}</h2><button type="button" disabled={busy} onClick={close} aria-label={ru ? 'Закрыть' : 'Close'}>×</button></header>
        <div className="signs-dialog-body">
          <p>{ru ? 'Знак будет виден 24 часа. Вы можете изменить выбор, не продлевая этот срок. Имя и комментарий увидят другие посетители.' : 'Your sign stays visible for 24 hours. You can change your choice without extending this period. Your name and comment are public.'}</p>
          {choice === 'flowers' ? <div className="signs-variant-grid" role="group" aria-label={ru ? 'Все виды цветов' : 'All flowers'}>
            {FLOWER_TYPES.flatMap(([type, label]) => FLOWER_COLORS.map(([color, colorLabel]) => <button type="button" key={`${type}-${color}`} className="signs-variant-tile" aria-pressed={flowerType === type && flowerColor === color} disabled={busy} onClick={() => { setFlowerType(type); setFlowerColor(color) }}><FlowerArtwork type={type} color={color} /><span>{ru ? `${colorLabel} ${label.toLowerCase()}` : `${color} ${type}`}</span></button>))}
          </div> : <div className="signs-variant-grid" role="group" aria-label={ru ? 'Все свечи' : 'All candles'}>{CANDLE_TYPES.map(([variant, label]) => <button type="button" key={variant} className="signs-variant-tile" aria-pressed={candle === variant} disabled={busy} onClick={() => setCandle(variant)}><MemorialCandle variant={variant} /><span>{ru ? label : variant.replaceAll('_', ' ')}</span></button>)}</div>}
          <div className={`signs-choice-preview signs-choice-preview-${choice}`}>{choice === 'flowers' ? <FlowerArtwork type={flowerType} color={flowerColor} /> : <MemorialCandle variant={candle} />}</div>
          <label htmlFor="sign-name">{ru ? 'Ваше имя (необязательно)' : 'Your name (optional)'}</label><input id="sign-name" maxLength={80} value={name} onChange={event => setName(event.target.value)} disabled={busy} />
          <label htmlFor="sign-comment">{ru ? 'Комментарий (необязательно)' : 'Comment (optional)'}</label><textarea id="sign-comment" maxLength={500} value={comment} onChange={event => setComment(event.target.value)} disabled={busy} /><small>{comment.length} / 500</small>
        </div>
        <footer className="signs-dialog-footer">{error && <p role="alert">{error}</p>}<div><button type="button" onClick={close} disabled={busy}>{ru ? 'Отмена' : 'Cancel'}</button><button type="submit" disabled={busy}>{busy ? (ru ? 'Сохраняем…' : 'Saving…') : (ru ? 'Оставить знак памяти' : 'Leave a sign')}</button></div></footer>
      </form>
    </dialog>
  </section>
}
export function MemorialSignsJournal({memorialId,lang,onClose}){
 const dialog=useRef(null),[data,setData]=useState(null),[offset,setOffset]=useState(0),[error,setError]=useState(''),ru=lang==='ru'
 useEffect(()=>{dialog.current.showModal()},[])
 useEffect(()=>{setData(null);setError('');apiClient.get(`/memorials/${memorialId}/signs/journal`,{params:{offset,limit:25}}).then(r=>setData(r.data)).catch(()=>setError(ru?'Не удалось загрузить журнал.':'Could not load the journal.'))},[offset,memorialId])
 return <dialog ref={dialog} className="signs-dialog signs-journal" aria-labelledby="journal-title" onCancel={onClose}><h2 id="journal-title">{ru?'Знаки памяти':'Signs of remembrance'}</h2>{error&&<p role="alert">{error}</p>}{!data&&!error?<p>{ru?'Загрузка…':'Loading…'}</p>:data&&<><div className="signs-table-wrap"><table><thead><tr><th>{ru?'Кто':'Who'}</th><th>{ru?'Знак':'Sign'}</th><th>{ru?'Комментарий':'Comment'}</th><th>{ru?'Когда':'When'}</th><th>{ru?'Состояние':'State'}</th></tr></thead><tbody>{data.items.map(e=><tr key={e.id}><td>{e.display_name||(ru?'Анонимный посетитель':'Anonymous visitor')}</td><td>{signDescription({...e,display_name:null},lang).split('. ')[0]}</td><td>{e.comment||'—'}</td><td>{new Date(e.created_at).toLocaleString(ru?'ru-RU':'en-US')}</td><td>{new Date(e.expires_at).getTime()>Date.now()?(ru?'Активно':'Active'):(ru?'Завершено':'Expired')}</td></tr>)}</tbody></table></div>{data.items.length===0&&<p>{ru?'Пока нет знаков памяти.':'No signs yet.'}</p>}<div><button disabled={offset===0} onClick={()=>setOffset(Math.max(0,offset-25))}>←</button><span>{data.total?offset+1:0}–{Math.min(offset+25,data.total)} / {data.total}</span><button disabled={offset+25>=data.total} onClick={()=>setOffset(offset+25)}>→</button></div></>}<button onClick={onClose}>{ru?'Закрыть':'Close'}</button></dialog>
}
