import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

// Отключаем предупреждение React DevTools в development
if (import.meta.env.DEV) {
  const originalWarn = console.warn
  console.warn = (...args) => {
    if (args[0]?.includes?.('Download the React DevTools')) {
      return // Игнорируем предупреждение о React DevTools
    }
    originalWarn(...args)
  }
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)

