import { Link } from 'react-router-dom'
import './Layout.css'

function Layout({ children }) {
  return (
    <div className="layout">
      <header className="header">
        <div className="container">
          <Link to="/" className="logo">
            <h1>Memorial MVP</h1>
          </Link>
          <nav className="nav">
            <Link to="/">Главная</Link>
            <Link to="/memorials/new">Создать мемориал</Link>
          </nav>
        </div>
      </header>
      <main className="main">
        <div className="container">{children}</div>
      </main>
      <footer className="footer">
        <div className="container">
          <p>&copy; 2024 Memorial MVP. Сохранение цифровой памяти.</p>
        </div>
      </footer>
    </div>
  )
}

export default Layout

