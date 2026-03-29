/**
 * Russian name declension utility
 * Supports prepositional ("о ком?") and instrumental ("с кем?") cases
 * for full Russian names: Имя [Отчество] Фамилия
 */

// Exceptions for names with floating vowels
const IRREGULAR_PREP = { 'пётр': 'Петре' }
const IRREGULAR_INST = { 'пётр': 'Петром' }

/** Detect gender from name parts using patronymic as the most reliable indicator */
function detectGender(parts) {
  for (const part of parts) {
    const p = part.toLowerCase()
    if (/вич$|ович$|евич$/.test(p)) return 'male'
    if (/вна$|овна$|евна$|ична$/.test(p)) return 'female'
  }
  const last = (parts[parts.length - 1] || '').toLowerCase()
  if (/[оеёа]ва$/.test(last)) return 'female'
  if (/[оеё]в$/.test(last)) return 'male'
  if (/ин$/.test(last)) return 'male'
  const first = (parts[0] || '').toLowerCase()
  if (/[ая]$/.test(first)) return 'female'
  return 'male'
}

function isPatronymic(word) {
  return /вич$|ович$|евич$|вна$|овна$|евна$|ична$/i.test(word)
}

function getWordType(word, index) {
  if (isPatronymic(word)) return 'patronymic'
  if (index === 0) return 'firstname'
  return 'surname'
}

function declinePrepositional(word, type, gender) {
  const key = word.toLowerCase()
  if (type === 'firstname' && IRREGULAR_PREP[key]) return IRREGULAR_PREP[key]

  if (type === 'firstname') {
    if (gender === 'female') {
      if (/ия$/i.test(word)) return word.slice(0, -1) + 'и'  // Мария → Марии
      if (/ья$/i.test(word)) return word.slice(0, -1) + 'е'  // Наталья → Наталье
      if (/ея$/i.test(word)) return word.slice(0, -1) + 'е'  // Пелагея → Пелагее
      if (/а$/i.test(word))  return word.slice(0, -1) + 'е'  // Светлана → Светлане
    } else {
      if (/ий$/i.test(word)) return word.slice(0, -1) + 'и'  // Василий → Василии
      if (/ей$/i.test(word)) return word.slice(0, -1) + 'е'  // Сергей → Сергее
      if (/й$/i.test(word))  return word.slice(0, -1) + 'е'  // Николай → Николае
      return word + 'е'                                        // Иван → Иване
    }
  }

  if (type === 'patronymic') {
    if (gender === 'female') {
      if (/вна$/i.test(word))  return word.slice(0, -1) + 'е' // Ивановна → Ивановне
      if (/ична$/i.test(word)) return word.slice(0, -1) + 'е' // Ильинична → Ильиничне
    } else {
      if (/вич$/i.test(word))  return word + 'е'              // Иванович → Ивановиче
    }
  }

  if (type === 'surname') {
    if (gender === 'female') {
      if (/[оеёа]ва$/i.test(word)) return word.slice(0, -1) + 'й' // Морозова → Морозовой
      if (/ина$/i.test(word))       return word.slice(0, -1) + 'й'
      if (/а$/i.test(word))         return word.slice(0, -1) + 'е'
    } else {
      if (/[оеё]в$/i.test(word))   return word + 'е'  // Морозов → Морозове
      if (/ин$/i.test(word))        return word + 'е'  // Пушкин → Пушкине
      if (/ский$/i.test(word))      return word.slice(0, -2) + 'ом'
      if (/цкий$/i.test(word))      return word.slice(0, -2) + 'ом'
    }
  }

  return word
}

function declineInstrumental(word, type, gender) {
  const key = word.toLowerCase()
  if (type === 'firstname' && IRREGULAR_INST[key]) return IRREGULAR_INST[key]

  if (type === 'firstname') {
    if (gender === 'female') {
      if (/ия$/i.test(word)) return word.slice(0, -1) + 'ей'  // Мария → Марией
      if (/ья$/i.test(word)) return word.slice(0, -1) + 'ей'  // Наталья → Натальей
      if (/ея$/i.test(word)) return word.slice(0, -1) + 'ей'  // Пелагея → Пелагеей
      if (/а$/i.test(word))  return word.slice(0, -1) + 'ой'  // Светлана → Светланой
    } else {
      if (/ий$/i.test(word)) return word.slice(0, -2) + 'ием' // Василий → Василием
      if (/ей$/i.test(word)) return word.slice(0, -1) + 'ем'  // Сергей → Сергеем
      if (/й$/i.test(word))  return word.slice(0, -1) + 'ем'  // Николай → Николаем
      const last = word.slice(-1).toLowerCase()
      if ('жшчщцъь'.includes(last)) return word + 'ем'        // мягкий/шипящий
      return word + 'ом'                                        // Иван → Иваном
    }
  }

  if (type === 'patronymic') {
    if (gender === 'female') {
      if (/вна$/i.test(word))  return word.slice(0, -1) + 'ой' // Ивановна → Ивановной
      if (/ична$/i.test(word)) return word.slice(0, -1) + 'ой' // Ильинична → Ильиничной
    } else {
      if (/вич$/i.test(word))  return word + 'ем'              // Иванович → Ивановичем
    }
  }

  if (type === 'surname') {
    if (gender === 'female') {
      if (/[оеёа]ва$/i.test(word)) return word.slice(0, -1) + 'й' // same as prepositional
      if (/ина$/i.test(word))       return word.slice(0, -1) + 'й'
      if (/а$/i.test(word))         return word.slice(0, -1) + 'ой'
    } else {
      if (/[оеё]в$/i.test(word))   return word + 'ым' // Морозов → Морозовым
      if (/ин$/i.test(word))        return word + 'ым' // Пушкин → Пушкиным
      if (/ский$/i.test(word))      return word.slice(0, -2) + 'им'
      if (/цкий$/i.test(word))      return word.slice(0, -2) + 'им'
    }
  }

  return word
}

/**
 * Decline a full Russian name to the specified case.
 * Preserves parenthetical notes like "(урождённая Попова)" unchanged.
 *
 * @param {string} fullName
 * @param {'prepositional'|'instrumental'} caseType
 * @returns {string}
 */
export function declineName(fullName, caseType = 'prepositional') {
  if (!fullName) return fullName

  // Separate main name from parenthetical
  const parenIdx = fullName.indexOf('(')
  const mainPart = parenIdx >= 0 ? fullName.slice(0, parenIdx).trim() : fullName.trim()
  const parenPart = parenIdx >= 0 ? ' ' + fullName.slice(parenIdx) : ''

  const parts = mainPart.split(/\s+/).filter(Boolean)
  if (!parts.length) return fullName

  const gender = detectGender(parts)
  const declineFn = caseType === 'instrumental' ? declineInstrumental : declinePrepositional

  const declined = parts.map((part, i) => {
    // Handle hyphenated surnames (e.g., Ковалёва-Морозова)
    if (part.includes('-')) {
      return part.split('-').map(sub => declineFn(sub, getWordType(sub, i), gender)).join('-')
    }
    return declineFn(part, getWordType(part, i), gender)
  })

  return declined.join(' ') + parenPart
}

/**
 * Returns "о/об [declined name]" (prepositional)
 * e.g. aboutName("Светлана Николаевна Морозова") → "о Светлане Николаевне Морозовой"
 */
export function aboutName(fullName) {
  if (!fullName) return 'нём'
  const declined = declineName(fullName, 'prepositional')
  const first = declined[0]?.toLowerCase() || ''
  const prep = 'аеёиоуыэюя'.includes(first) ? 'об' : 'о'
  return `${prep} ${declined}`
}

/**
 * Returns declined name in instrumental (for "Чат с [name]")
 * e.g. instrumentalName("Светлана Николаевна Морозова") → "Светланой Николаевной Морозовой"
 */
export function instrumentalName(fullName) {
  if (!fullName) return fullName
  return declineName(fullName, 'instrumental')
}
