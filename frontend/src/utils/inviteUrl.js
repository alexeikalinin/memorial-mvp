/**
 * Ссылка на страницу contribute с учётом Vite base (/ в dev, /app/ на Vercel).
 * Надёжнее, чем invite_url с бэкенда, если PUBLIC_FRONTEND_URL указывал на localhost.
 */
export function buildContributeInviteUrl(token) {
  if (!token) return ''
  const base = import.meta.env.BASE_URL || '/'
  const prefix = base === '/' ? '' : base.replace(/\/$/, '')
  if (typeof window !== 'undefined' && window.location?.origin) {
    return `${window.location.origin}${prefix}/contribute/${token}`
  }
  return `/contribute/${token}`
}
