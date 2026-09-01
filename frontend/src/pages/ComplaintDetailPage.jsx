import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useDispatch, useSelector } from 'react-redux'
import ReactMarkdown from 'react-markdown'
import { fetchComplaint, runPipeline } from '../store/complaintsSlice'
import { getAiTrace, createCapa, listCapaForComplaint } from '../api/client'
import SeverityBadge from '../components/SeverityBadge'

export default function ComplaintDetailPage() {
  const { id } = useParams()
  const dispatch = useDispatch()
  const { selected, pipelineRunning } = useSelector((s) => s.complaints)
  const [trace, setTrace] = useState(null)
  const [capaItems, setCapaItems] = useState([])
  const [addingCapa, setAddingCapa] = useState(null)

  useEffect(() => {
    dispatch(fetchComplaint(id))
    listCapaForComplaint(id).then(setCapaItems).catch(() => {})
  }, [dispatch, id])

  const handleRunPipeline = async () => {
    await dispatch(runPipeline(id)).unwrap()
    const t = await getAiTrace(id)
    setTrace(t.trace)
  }

  const handleAddCapa = async (actionType, description) => {
    setAddingCapa(description)
    try {
      const capa = await createCapa({
        complaint_id: id,
        action_type: actionType,
        description,
      })
      setCapaItems((prev) => [...prev, capa])
    } finally {
      setAddingCapa(null)
    }
  }

  const isCapaSaved = (description) => capaItems.some((c) => c.description === description)

  if (!selected) return <p>Loading…</p>

  return (
    <div>
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h2 style={{ margin: 0 }}>{selected.product_name}</h2>
            <p style={{ color: 'var(--color-muted)' }}>
              Batch: {selected.batch_number || '—'} · Customer: {selected.customer_name || '—'}
            </p>
          </div>
          <SeverityBadge severity={selected.severity} />
        </div>
        <p>{selected.description}</p>

        <button className="primary" onClick={handleRunPipeline} disabled={pipelineRunning}>
          {pipelineRunning ? 'Running AI pipeline…' : 'Run AI Pipeline'}
        </button>
      </div>

      {selected.completeness_flags && (
        <div className="card">
          <h3>Completeness Check</h3>
          <pre style={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(selected.completeness_flags, null, 2)}</pre>
        </div>
      )}

      {selected.duplicate_of && (
        <div className="card" style={{ borderColor: 'var(--severity-medium)' }}>
          <h3>⚠ Possible Duplicate</h3>
          <p>This complaint appears similar to complaint <code>{selected.duplicate_of}</code></p>
        </div>
      )}

      {selected.root_cause_suggestion && (
        <div className="card">
          <h3>Root Cause Suggestion</h3>
          <ReactMarkdown>{selected.root_cause_suggestion}</ReactMarkdown>
        </div>
      )}

      {selected.ai_summary && (
        <div className="card">
          <h3>AI Summary</h3>
          <ReactMarkdown>{selected.ai_summary}</ReactMarkdown>
        </div>
      )}

      {selected.capa_suggestions && (
        <div className="card">
          <h3>CAPA Suggestions</h3>
          {['corrective', 'preventive'].map((type) => (
            <div key={type} style={{ marginBottom: 12 }}>
              <strong style={{ textTransform: 'capitalize' }}>{type}</strong>
              {(selected.capa_suggestions[type] || []).map((desc, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid #f3f4f6' }}>
                  <span style={{ fontSize: 14 }}>{desc}</span>
                  <button
                    className="primary"
                    style={{ fontSize: 12, padding: '4px 10px', flexShrink: 0, marginLeft: 12 }}
                    disabled={isCapaSaved(desc) || addingCapa === desc}
                    onClick={() => handleAddCapa(type, desc)}
                  >
                    {isCapaSaved(desc) ? '✓ Added' : addingCapa === desc ? 'Adding…' : '+ Track as CAPA'}
                  </button>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}

      {capaItems.length > 0 && (
        <div className="card">
          <h3>Tracked CAPA Actions</h3>
          {capaItems.map((c) => (
            <div key={c.id} style={{ padding: '8px 0', borderBottom: '1px solid #f3f4f6' }}>
              <span className="badge" style={{ background: '#374151', marginRight: 8 }}>{c.action_type}</span>
              <span className="badge" style={{ background: '#9ca3af', marginRight: 8 }}>{c.status}</span>
              {c.description}
            </div>
          ))}
        </div>
      )}

      {trace && (
        <div className="card">
          <h3>Pipeline Trace</h3>
          {trace.map((step, i) => (
            <div key={i} className="trace-step">
              <strong>{step.step}</strong>
              <div style={{ color: 'var(--color-muted)', fontSize: 14 }}>{step.detail}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
