import { Routes, Route, Link } from 'react-router-dom'
import ComplaintListPage from './pages/ComplaintListPage'
import AiIntakePage from './pages/AiIntakePage'
import ComplaintDetailPage from './pages/ComplaintDetailPage'

export default function App() {
  return (
    <div>
      <header style={{ borderBottom: '1px solid #e5e7eb', background: 'white' }}>
        <div className="container" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Link to="/" style={{ textDecoration: 'none', color: '#111827', fontWeight: 700, fontSize: 18 }}>
            AIVOA · Complaint Management
          </Link>
          <Link to="/new">
            <button className="primary">+ New Complaint</button>
          </Link>
        </div>
      </header>

      <div className="container" style={{ maxWidth: 1300 }}>
        <Routes>
          <Route path="/" element={<ComplaintListPage />} />
          <Route path="/new" element={<AiIntakePage />} />
          <Route path="/complaints/:id" element={<ComplaintDetailPage />} />
        </Routes>
      </div>
    </div>
  )
}
