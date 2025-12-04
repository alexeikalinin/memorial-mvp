import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'
import MemorialCreate from './pages/MemorialCreate'
import MemorialDetail from './pages/MemorialDetail'

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
        </Routes>
      </Layout>
    </Router>
  )
}

export default App

