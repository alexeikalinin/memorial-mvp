import { useState } from 'react'
import { accessAPI } from '../api/client'
import { useLanguage } from '../contexts/LanguageContext'

export default function OwnershipTransferPanel({ memorialId, isOwner }) {
  const { lang } = useLanguage()
  const ru = lang === 'ru'
  const [email, setEmail] = useState('')
  const [keepEditor, setKeepEditor] = useState(true)
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  const [confirming, setConfirming] = useState(false)
  if (!isOwner) return null
  const submit = async () => {
    setBusy(true)
    setMessage('')
    try {
      await accessAPI.transfer(memorialId, { email: email.trim(), keep_editor: keepEditor })
      setMessage(ru ? 'Предложение отправлено. Владение изменится только после принятия получателем.' : 'Proposal sent. Ownership changes only after the recipient accepts.')
      setConfirming(false)
      setEmail('')
    } catch (error) {
      setMessage(error.response?.data?.detail || (ru ? 'Не удалось отправить предложение.' : 'Could not send proposal.'))
    } finally { setBusy(false) }
  }
  return <section className="invite-form">
    <h4>{ru ? 'Передать владение мемориалом' : 'Transfer memorial ownership'}</h4>
    <p>{ru ? 'Для совместного наполнения достаточно прав редактора. Передача владения позволит получателю управлять доступом и удалять страницу. Получатель должен зарегистрироваться и подтвердить почту.' : 'Editor access is enough to contribute together. Ownership lets the recipient manage access and delete this page. The recipient must register and verify their email.'}</p>
    <label>{ru ? 'Почта нового владельца' : 'New owner email'}<input type="email" value={email} onChange={e => { setEmail(e.target.value); setConfirming(false) }} disabled={busy} /></label>
    <label style={{ display: 'flex', gap: 8 }}><input type="checkbox" checked={keepEditor} onChange={e => { setKeepEditor(e.target.checked); setConfirming(false) }} disabled={busy} />{ru ? 'Оставить мне права редактора' : 'Keep my editor access'}</label>
    {confirming ? <div>
      <p>{ru ? `Передать владение ${email.trim()}? ${keepEditor ? 'Вы останетесь редактором.' : 'Ваш доступ будет отозван.'}` : `Transfer ownership to ${email.trim()}? ${keepEditor ? 'You will remain an editor.' : 'Your access will be removed.'}`}</p>
      <button className="btn btn-primary" disabled={busy} onClick={submit}>{ru ? 'Отправить предложение' : 'Send proposal'}</button>
      <button className="btn" disabled={busy} onClick={() => setConfirming(false)}>{ru ? 'Отмена' : 'Cancel'}</button>
    </div> : <button className="btn" disabled={busy || !email.trim() || !email.includes('@')} onClick={() => setConfirming(true)}>{ru ? 'Продолжить' : 'Continue'}</button>}
    {message && <p role="status">{message}</p>}
  </section>
}
