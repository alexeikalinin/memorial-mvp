import { useState, useEffect, useCallback } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { billingAPI } from '../api/client'
import { useLanguage } from '../contexts/LanguageContext'
import { safeReturn } from '../utils/authReturn'
import './AuthPage.css'
import './PricingPage.css'

import plans from '../data/planCatalog.json'

export default function PricingPage() {
  const { lang } = useLanguage()
  const ru = lang !== 'en'
  const [params] = useSearchParams()
  const next = safeReturn(params.get('next'))
  const [usage, setUsage] = useState(null)
  const [error, setError] = useState('')
  const loadUsage = useCallback(() => {
    setError('')
    billingAPI.usage().then(res => setUsage(res.data)).catch(() => setError(ru ? 'Не удалось проверить тариф. Попробуйте ещё раз.' : 'Could not check your plan. Please retry.'))
  }, [ru])
  useEffect(() => { loadUsage() }, [loadUsage])
  const active = usage?.plan && usage.plan !== 'free'
  return <div className="auth-page"><div className="auth-card pricing-catalog">
    <h1>{ru ? 'Тарифы vspomin.ai' : 'vspomin.ai plans'}</h1>
    <p>{ru ? 'Новые тарифы готовятся к запуску. Сейчас можно оставить заявку без оплаты.' : 'New plans are being prepared for launch. You can register your interest without payment.'}</p>
    <p>{ru ? 'Бесплатно: 1 мемориал · 15 текстовых AI-ответов в месяц · фотографии, истории и приглашения.' : 'Free: 1 memorial · 15 text AI replies per month · photos, stories and invitations.'}</p>
    <div className="pricing-catalog-grid">
      {plans.map(plan => <article className="pricing-catalog-plan" key={plan.name}>
        <h2>{plan.name}</h2>
        <p className="pricing-catalog-price">${plan.price} <span>{ru ? '/ год' : '/ year'}</span></p>
        <ul>
          <li>{ru ? `До ${plan.pages} мемориалов` : `Up to ${plan.pages} memorials`}</li>
          <li>{ru ? `${plan.storage} ГБ на аккаунт` : `${plan.storage} GB per account`}</li>
          <li>{ru ? `${plan.text} текстовых AI-ответов в месяц` : `${plan.text} text AI replies per month`}</li>
          <li>{ru ? `До ${plan.clones} клонов голоса` : `Up to ${plan.clones} voice clones`}</li>
          <li>{ru ? `Около ${plan.voice} минут озвучивания в месяц` : `About ${plan.voice} voice minutes per month`}</li>
        </ul>
        <a className="btn btn-primary" href="/#pricing">{ru ? 'Оставить заявку' : 'Register interest'}</a>
      </article>)}
      <article className="pricing-catalog-plan">
        <h2>Lifetime</h2>
        <p className="pricing-catalog-price">{ru ? 'Индивидуально' : 'Custom pricing'}</p>
        <ul>
          <li>{ru ? 'Мемориалы и объём архива — по соглашению' : 'Memorial count and archive size by agreement'}</li>
          <li>{ru ? 'Срок хранения и текстовый AI согласуем отдельно' : 'Storage term and text AI allowance agreed separately'}</li>
          <li>{ru ? 'Голосовые ответы оплачиваются отдельно' : 'Voice replies are charged separately'}</li>
          <li>{ru ? 'Разовая оплата согласованного пакета' : 'One-time payment for the agreed package'}</li>
        </ul>
        <a className="btn btn-primary" href="/#pricing">{ru ? 'Обсудить Lifetime' : 'Discuss Lifetime'}</a>
      </article>
    </div>
    <p>{ru ? 'Лимиты общие для аккаунта и всех его мемориалов. Текстовые ответы и минуты голоса обновляются ежемесячно, не накапливаются. Минуты озвучивания ориентировочные. Видео не включено и пока недоступно.' : 'Limits are shared across the account and its memorials. Text replies and voice minutes renew monthly and do not roll over. Voice minutes are approximate. Video is not included and is currently unavailable.'}</p>
    {usage && <p>{ru ? 'Текущий тариф: ' : 'Current plan: '}{usage.plan} · {usage.chat_messages_used}/{usage.chat_messages_limit ?? '∞'} {ru ? 'текстовых ответов за месяц' : 'text replies this month'}</p>}
    {params.get('checkout') === 'success' && <p role="status">{active ? (ru ? 'Тариф активирован. Можно вернуться к разговору.' : 'Your plan is active. Return to your conversation.') : (ru ? 'Ждём подтверждение оплаты. Обновите статус через несколько секунд.' : 'Waiting for payment confirmation. Refresh the status in a few seconds.')}</p>}
    {params.get('checkout') === 'cancel' && <p>{ru ? 'Оплата отменена. Ваш тариф не изменился.' : 'Payment cancelled. Your plan has not changed.'}</p>}
    {error && <p role="alert">{error}</p>}
    <button className="btn btn-secondary" onClick={loadUsage}>{ru ? 'Обновить статус' : 'Refresh status'}</button>
    <p><Link to={next}>{ru ? 'Вернуться к мемориалу' : 'Return to the memorial'}</Link></p>
  </div></div>
}
