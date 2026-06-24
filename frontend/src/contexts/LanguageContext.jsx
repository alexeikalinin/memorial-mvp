import { createContext, useContext, useState, useEffect } from 'react'
import ru from '../locales/ru'
import en from '../locales/en'

const translations = { ru, en }

/** Запуск на русскоязычном рынке: RU — дефолт, EN временно скрыт в шапке приложения.
 *  Вернуть `true`, чтобы снова показать переключатель EN. */
export const SHOW_EN_LANGUAGE_OPTION = false

function readInitialLang() {
  if (!SHOW_EN_LANGUAGE_OPTION) {
    if (localStorage.getItem('lang') === 'en') localStorage.setItem('lang', 'ru')
    return 'ru'
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
    if (!SHOW_EN_LANGUAGE_OPTION) {
      if (newLang === 'ru') {
        setLangState('ru')
        localStorage.setItem('lang', 'ru')
      }
      return
    }
    setLangState(newLang)
    localStorage.setItem('lang', newLang)
  }

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

  useEffect(() => {
    if (typeof document !== 'undefined') {
      document.documentElement.lang = lang === 'en' ? 'en' : 'ru'
      document.title = t('nav.page_title')
    }
  }, [lang])

  return (
    <LanguageContext.Provider value={{ lang, setLang, t }}>
      {children}
    </LanguageContext.Provider>
  )
}

export const useLanguage = () => useContext(LanguageContext)
