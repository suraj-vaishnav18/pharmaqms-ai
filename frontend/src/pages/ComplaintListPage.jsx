import { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { Link } from 'react-router-dom'
import { fetchComplaints } from '../store/complaintsSlice'
import SeverityBadge from '../components/SeverityBadge'

export default function ComplaintListPage() {
  const dispatch = useDispatch()
  const { items, status } = useSelector((s) => s.complaints)

  useEffect(() => {
    dispatch(fetchComplaints())
  }, [dispatch])

  if (status === 'loading') return <p>Loading complaints…</p>

  return (
    <div>
      <h2>Complaints</h2>
      {items.length === 0 && <p style={{ color: 'var(--color-muted)' }}>No complaints yet. Create one to get started.</p>}
      {items.map((c) => (
        <Link key={c.id} to={`/complaints/${c.id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
          <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontWeight: 600 }}>{c.product_name}</div>
              <div style={{ color: 'var(--color-muted)', fontSize: 14 }}>{c.description.slice(0, 100)}...</div>
            </div>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <SeverityBadge severity={c.severity} />
              <span className="badge" style={{ background: '#374151' }}>{c.status}</span>
            </div>
          </div>
        </Link>
      ))}
    </div>
  )
}
