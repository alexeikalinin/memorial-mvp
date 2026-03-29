import { createContext, useContext, useState, useEffect } from 'react'
import ru from '../locales/ru'
import en from '../locales/en'

const translations = { ru, en }

/** Временно `false` для демо инвестору (только EN в шапке); вернуть `true`, чтобы снова показать RU. */
export const SHOW_RU_LANGUAGE_OPTION = false

function readInitialLang() {
  if (!SHOW_RU_LANGUAGE_OPTION) {
    if (localStorage.getItem('lang') === 'ru') localStorage.setItem('lang', 'en')
    return 'en'
  }
  return localStorage.getItem('lang') || 'ru'
}

const LanguageContext = createContext({
  lang: 'ru',
  setLang: () => {},
  t: (key) => key,
})

export function LanguageProvider({ children }) {
  const [lang, setLangState] = useState(readInitialLang)

  const setLang = (newLang) => {
    if (!SHOW_RU_LANGUAGE_OPTION) {
      if (newLang === 'en') {
        setLangState('en')
        localStorage.setItem('lang', 'en')
      }
      return
    }
    setLangState(newLang)
    localStorage.setItem('lang', newLang)
  }

  useEffect(() => {
    if (typeof document !== 'undefined') {
      document.documentElement.lang = lang === 'en' ? 'en' : 'ru'
    }
  }, [lang])

  const t = (key, params = {}) => {
    const keys = key.split('.')
    let val = translations[lang]
    for (const k of keys) {
      val = val?.[k]
    }
    if (typeof val === 'string' && Object.keys(params).length > 0) {
      return Object.entries(params).reduce(
        (s, [k, v]) => s.replace(`{${k}}`, v),
        val
      )
    }
    return val ?? key
  }

  return (
    <LanguageContext.Provider value={{ lang, setLang, t }}>
      {children}
    </LanguageContext.Provider>
  )
}

export const useLanguage = () => useContext(LanguageContext)
