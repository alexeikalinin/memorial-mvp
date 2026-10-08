import { useState, useEffect, useCallback } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { billingAPI } from '../api/client'
import { useLanguage } from '../contexts/LanguageContext'
import { safeReturn } from '../utils/authReturn'
import './AuthPage.css'

export default function PricingPage() {
  const { lang } = useLanguage()
  const ru = lang !== 'en'
  const [params] = useSearchParams()
  const next = safeReturn(params.get('next'))
  const [usage, setUsage] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const loadUsage = useCallback(() => billingAPI.usage().then(res => setUsage(res.data)).catch(() => setError(ru ? 'Не удалось проверить тариф. Попробуйте ещё раз.' : 'Could not check your plan. Please retry.')), [ru])
  useEffect(() => { loadUsage() }, [loadUsage])
  const checkout = async () => {
    setLoading(true); setError('')
    try {
      const base = `${window.location.origin}${import.meta.env.BASE_URL === '/' ? '' : import.meta.env.BASE_URL.replace(/\/$/, '')}`
      const query = `next=${encodeURIComponent(next)}`
      const res = await billingAPI.checkout({ plan: 'plus_monthly', success_url: `${base}/pricing?${query}&checkout=success`, cancel_url: `${base}/pricing?${query}&checkout=cancel` })
      window.location.assign(res.data.checkout_url)
    } catch {
      setError(ru ? 'Оплата пока недоступна. Доступ не изменён — попробуйте позже.' : 'Payment is currently unavailable. Your access has not changed; please try later.')
    } finally { setLoading(false) }
  }
  const active = usage?.plan && usage.plan !== 'free'
  return <div className="auth-page"><div className="auth-card">
    <h1>{ru ? 'Продолжить разговор' : 'Continue the conversation'}</h1>
    <p>{ru ? 'Бесплатно: 15 текстовых вопросов в месяц на аккаунт. Лимит обновляется 1-го числа.' : 'Free: 15 text questions per month per account. Resets on the first day of each month.'}</p>
    <h2>Plus</h2>
    <p>{ru ? '200 вопросов в месяц. Стоимость и условия подписки будут показаны перед оплатой.' : '200 questions per month. Subscription price and terms are shown before payment.'}</p>
    {params.get('checkout') === 'success' && <p role="status">{active ? (ru ? 'Тариф активирован. Можно вернуться к разговору.' : 'Your plan is active. Return to your conversation.') : (ru ? 'Ждём подтверждение оплаты. Обновите статус через несколько секунд.' : 'Waiting for payment confirmation. Refresh the status in a few seconds.')}</p>}
    {params.get('checkout') === 'cancel' && <p>{ru ? 'Оплата отменена. Ваш тариф не изменился.' : 'Payment cancelled. Your plan has not changed.'}</p>}
    {error && <p role="alert">{error}</p>}
    {!active && <button className="btn btn-primary" disabled={loading || !usage} onClick={checkout}>{loading ? (ru ? 'Открываем оплату…' : 'Opening checkout…') : (ru ? 'Перейти к оплате Plus' : 'Subscribe to Plus')}</button>}
    <button className="btn btn-secondary" onClick={loadUsage}>{ru ? 'Обновить статус' : 'Refresh status'}</button>
    <p><Link to={next}>{ru ? 'Вернуться к мемориалу' : 'Return to the memorial'}</Link></p>
  </div></div>
}
