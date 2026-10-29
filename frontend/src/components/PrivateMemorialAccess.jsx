import {useState} from 'react'
import {Link} from 'react-router-dom'
import {useAuth} from '../context/AuthContext'
import {useLanguage} from '../contexts/LanguageContext'
import {accessAPI} from '../api/client'
export default function PrivateMemorialAccess({memorialId}){
 const {user}=useAuth(),{lang}=useLanguage(),en=lang==='en'
 const [role,setRole]=useState('viewer'),[message,setMessage]=useState(''),[busy,setBusy]=useState(false),[sent,setSent]=useState(false),[error,setError]=useState('')
 const submit=async e=>{e.preventDefault();setBusy(true);setError('');try{await accessAPI.requestAccess(memorialId,{requested_role:role,message});setSent(true)}catch(err){setError(typeof err.response?.data?.detail==='string'?err.response.data.detail:en?'Could not send the request. Please retry.':'Не удалось отправить запрос. Попробуйте ещё раз.')}finally{setBusy(false)}}
 return <section className="public-request-access"><h1>{en?'Private memorial':'Закрытый мемориал'}</h1><p>{en?'The owner has limited access. The contents remain hidden until access is granted.':'Владелец ограничил доступ. Содержимое скрыто до выдачи разрешения.'}</p>
 {!user?<Link className="btn btn-primary" to={`/login?next=${encodeURIComponent(`/m/${memorialId}`)}`}>{en?'Sign in to request access':'Войти и запросить доступ'}</Link>:sent?<p role="status">{en?'Request sent. The owner must approve it before you can access the memorial.':'Запрос отправлен. Доступ появится после одобрения владельцем.'}</p>:<form onSubmit={submit}>
 <label htmlFor="private-access-role">{en?'Requested access':'Какой доступ нужен?'}</label><select id="private-access-role" value={role} disabled={busy} onChange={e=>setRole(e.target.value)}><option value="viewer">{en?'View only':'Только просматривать'}</option><option value="editor">{en?'Edit and contribute':'Дополнять и редактировать'}</option></select>
 <label htmlFor="private-access-message">{en?'Message to the owner (optional)':'Кем вы приходитесь человеку? Пояснение для владельца (необязательно)'}</label><textarea id="private-access-message" maxLength={2000} value={message} disabled={busy} onChange={e=>setMessage(e.target.value)}/>
 {error&&<p role="alert">{error}</p>}<button type="submit" className="btn btn-primary" disabled={busy}>{busy?(en?'Sending…':'Отправляем…'):(en?'Request access':'Запросить доступ')}</button></form>}
 </section>
}
