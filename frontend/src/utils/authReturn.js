export function safeReturn(value, fallback = '/') {
  return typeof value === 'string' && value.startsWith('/') && !value.startsWith('//') && !value.includes('\\') && !Array.from(value).some(char => char.charCodeAt(0) < 32) ? value : fallback
}
