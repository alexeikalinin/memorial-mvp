import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { accessAPI, familyAPI } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { useLanguage } from '../contexts/LanguageContext'

export default function FamilyNotifications() {
  const { user } = useAuth()
  const userId = user?.id
  const { lang } = useLanguage()
  const ru = lang === 'ru'
  const [transfers, setTransfers] = useState([])
  const [requests, setRequests] = useState([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  useEffect(() => {
    let active = true
    setError('')
    if (!userId) { setTransfers([]); setRequests([]); return }
    Promise.all([accessAPI.transfers(), familyAPI.getRequests()]).then(([a, b]) => {
      if (active) { setTransfers(a.data.filter(x => x.status === 'pending')); setRequests(b.data.filter(x => x.status === 'pending' && x.can_respond)) }
    }).catch(() => { if (active) setError(ru ? 'Не удалось загрузить семейные запросы.' : 'Could not load family requests.') })
    return () => { active = false }
  }, [userId, ru])
  const respond = async (row, decision) => {
    setBusy(true)
    setError('')
    try {
      await accessAPI.respondTransfer(row.id, { decision })
      setTransfers(prev => prev.filter(x => x.id !== row.id))
    } catch (e) { setError(e.response?.data?.detail || (ru ? 'Не удалось обработать предложение.' : 'Could not review proposal.')) }
    finally { setBusy(false) }
  }
  if (!transfers.length && !requests.length && !error) return null
  return <section className="family-notifications" style={{ padding: '1rem', border: '1px solid var(--border)', borderRadius: 12, marginBottom: '1rem' }}>
    <h3>{ru ? 'Семейные запросы' : 'Family requests'}</h3>
    {requests.map(row => <p key={'link' + row.id}>{row.memorial_name} ↔ {row.related_memorial_name} — <Link to={`/memorials/${row.related_memorial_id}?tab=family`}>{ru ? 'Рассмотреть родственную связь' : 'Review family link'}</Link></p>)}
    {transfers.map(row => <div key={row.id} style={{ marginBottom: 12 }}>
      <strong>{row.memorial_name}</strong>
      {row.to_user_id === user?.id ? <>
        <p>{ru ? 'Вам предлагают стать владельцем этой страницы. Вы сможете управлять доступом и удалять мемориал.' : 'You are invited to own this page, including managing access and deleting the memorial.'}</p>
        <button className="btn btn-primary" disabled={busy} onClick={() => respond(row, 'accept')}>{ru ? 'Принять владение' : 'Accept ownership'}</button>
        <button className="btn" disabled={busy} onClick={() => respond(row, 'reject')}>{ru ? 'Отклонить' : 'Reject'}</button>
      </> : <><p>{ru ? `Ожидает принятия: ${row.recipient_email}` : `Awaiting acceptance: ${row.recipient_email}`}</p><button className="btn" disabled={busy} onClick={() => respond(row, 'cancel')}>{ru ? 'Отменить предложение' : 'Cancel proposal'}</button></>}
    </div>)}
    {error && <p role="alert">{error}</p>}
  </section>
}
