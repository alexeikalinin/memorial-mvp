/**
 * Приводит ввод к YYYY-MM-DD или возвращает null, если строка непустая и невалидна.
 * Поддержка: YYYY-MM-DD, DD.MM.YYYY
 */
export function normalizeFlexibleDateInput(s) {
  const v = (s || '').trim()
  if (!v) return ''
  const iso = /^(\d{4})-(\d{2})-(\d{2})$/.exec(v)
  if (iso) {
    const y = Number(iso[1])
    const m = Number(iso[2])
    const d = Number(iso[3])
    const dt = new Date(y, m - 1, d)
    if (dt.getFullYear() !== y || dt.getMonth() !== m - 1 || dt.getDate() !== d) return null
    return `${iso[1]}-${iso[2]}-${iso[3]}`
  }
  const dmy = /^(\d{1,2})\.(\d{1,2})\.(\d{4})$/.exec(v)
  if (dmy) {
    const dd = String(dmy[1]).padStart(2, '0')
    const mm = String(dmy[2]).padStart(2, '0')
    const yyyy = dmy[3]
    const y = Number(yyyy)
    const mo = Number(mm)
    const da = Number(dd)
    const dt = new Date(y, mo - 1, da)
    if (dt.getFullYear() !== y || dt.getMonth() !== mo - 1 || dt.getDate() !== da) return null
    return `${yyyy}-${mm}-${dd}`
  }
  return null
}

/** Пустая строка → ok; непустое невалидное → error */
export function parseDateFieldForSubmit(raw) {
  const v = (raw || '').trim()
  if (!v) return { ok: true, iso: null }
  const n = normalizeFlexibleDateInput(v)
  if (n === null || n === '') return { ok: false, iso: null }
  return { ok: true, iso: n }
}
