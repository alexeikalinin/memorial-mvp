import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'
import MemorialCreate from './pages/MemorialCreate'
import MemorialDetail from './pages/MemorialDetail'
import MemorialPublic from './pages/MemorialPublic'
import ContributePage from './pages/ContributePage'

function App() {
  return (
    <Router
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true,
      }}
    >
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/memorials/new" element={<MemorialCreate />} />
          <Route path="/memorials/:id" element={<MemorialDetail />} />
          <Route path="/m/:id" element={<MemorialPublic />} />
          <Route path="/contribute/:token" element={<ContributePage />} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App

