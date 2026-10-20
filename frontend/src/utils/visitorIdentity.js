const fallbackIds = new Map()
export function getVisitorId(key) {
  let saved
  try { saved = localStorage.getItem(key) } catch { /* Storage can be restricted in private browsing. */ }
  if (saved) return saved
  if (fallbackIds.has(key)) return fallbackIds.get(key)
  const id = globalThis.crypto?.randomUUID?.() || 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const byte = globalThis.crypto?.getRandomValues ? crypto.getRandomValues(new Uint8Array(1))[0] : Math.floor(Math.random() * 256)
    return (c === 'x' ? byte & 15 : (byte & 3) | 8).toString(16)
  })
  fallbackIds.set(key, id)
  try { localStorage.setItem(key, id) } catch { /* The in-memory identity still works for this tab. */ }
  return id
}
