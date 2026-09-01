import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { copilotExtractText, copilotExtractFile, copilotChat, createComplaint } from '../api/client'

const FIELD_LABELS = {
  complaint_source: 'Complaint Source',
  customer_name: 'Customer Name',
  product_name: 'Product Name',
  product_strength: 'Product Strength / Grade',
  batch_number: 'Batch / Lot Number',
  manufacturing_date: 'Manufacturing Date',
  expiry_date: 'Expiry Date',
  affected_quantity: 'Affected Quantity',
  complaint_category: 'Complaint Category',
  complaint_description: 'Complaint Description',
}

const AI_FIELDS = {
  severity_suggested: 'Severity (Suggested)',
  suggested_next_action: 'Suggested Next Action',
  initial_risk_assessment: 'Initial Risk Assessment',
}

const EMPTY_FIELDS = Object.fromEntries(
  [...Object.keys(FIELD_LABELS), ...Object.keys(AI_FIELDS)].map((k) => [k, null])
)

export default function AiIntakePage() {
  const navigate = useNavigate()
  const [fields, setFields] = useState(EMPTY_FIELDS)
  const [changedKeys, setChangedKeys] = useState(new Set())
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: 'Ready to process new complaints. You can paste the raw email from the customer, or upload a PDF of the complaint report. I will extract the data and run the initial risk assessment.',
    },
  ])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const [saving, setSaving] = useState(false)
  const fileInputRef = useRef(null)

  const hasAnyData = Object.values(fields).some((v) => v)

  const applyNewFields = (newFields) => {
    const changed = new Set()
    Object.entries(newFields).forEach(([k, v]) => {
      if (v && v !== fields[k]) changed.add(k)
    })
    setFields((prev) => ({ ...prev, ...newFields }))
    setChangedKeys(changed)
    setTimeout(() => setChangedKeys(new Set()), 2000)
  }

  const handleSend = async () => {
    const text = input.trim()
    if (!text || busy) return
    setMessages((m) => [...m, { role: 'user', text }])
    setInput('')
    setBusy(true)
    try {
      const result = hasAnyData
        ? await copilotChat(text, fields)
        : await copilotExtractText(text)
      applyNewFields(result.fields)
      setMessages((m) => [...m, { role: 'assistant', text: result.assistant_message }])
    } catch (err) {
      setMessages((m) => [...m, { role: 'assistant', text: 'Sorry, something went wrong parsing that. Please try again.' }])
    } finally {
      setBusy(false)
    }
  }

  const handleFile = async (file) => {
    if (!file) return
    setMessages((m) => [...m, { role: 'user', text: `📄 ${file.name}`, isFile: true }])
    setBusy(true)
    try {
      const result = await copilotExtractFile(file)
      applyNewFields(result.fields)
      setMessages((m) => [...m, { role: 'assistant', text: result.assistant_message }])
    } catch (err) {
      const detail = err?.response?.data?.detail || 'Could not process this file.'
      setMessages((m) => [...m, { role: 'assistant', text: detail }])
    } finally {
      setBusy(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files?.[0]
    if (file) handleFile(file)
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      const complaint = await createComplaint({
        product_name: fields.product_name || 'Unknown product',
        batch_number: fields.batch_number,
        customer_name: fields.customer_name,
        channel: fields.complaint_source || 'portal',
        description: fields.complaint_description || 'No description extracted',
        intake_details: fields,
      })
      navigate(`/complaints/${complaint.id}`)
    } finally {
      setSaving(false)
    }
  }

  const fieldClass = (key) =>
    'copilot-field' + (changedKeys.has(key) ? ' copilot-field-updated' : '')

  return (
    <div className="copilot-layout">
      <style>{`
        .copilot-layout { display: grid; grid-template-columns: 1.3fr 1fr; gap: 20px; align-items: start; }
        .copilot-field { transition: background 0.6s; border-radius: 6px; padding: 2px 4px; margin: -2px -4px; }
        .copilot-field-updated { background: #d1fae5; }
        .copilot-field label { display:block; font-size: 12px; font-weight: 600; color: var(--color-muted); margin-bottom: 4px; }
        .copilot-field-value { min-height: 20px; font-size: 14px; }
        .copilot-field-value.empty { color: #9ca3af; font-style: italic; }
        .field-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 18px; }
        .chat-panel { display: flex; flex-direction: column; height: 620px; }
        .chat-log { flex: 1; overflow-y: auto; padding: 4px; }
        .chat-bubble { max-width: 85%; padding: 10px 14px; border-radius: 12px; margin-bottom: 10px; font-size: 14px; line-height: 1.4; }
        .chat-bubble.user { background: var(--color-primary); color: white; margin-left: auto; }
        .chat-bubble.assistant { background: #f3f4f6; color: var(--color-text); }
        .dropzone { border: 2px dashed #cbd5e1; border-radius: 10px; padding: 24px; text-align: center; color: var(--color-muted); font-size: 14px; cursor: pointer; margin-bottom: 12px; }
        .dropzone.drag-over { border-color: var(--color-primary); background: #eff6ff; }
        .chat-input-row { display: flex; gap: 8px; margin-top: 10px; }
        .chat-input-row input { margin-bottom: 0; flex: 1; }
      `}</style>

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ margin: 0 }}>Log Customer Complaint</h2>
            <p style={{ color: 'var(--color-muted)', margin: '4px 0 0' }}>API & FDF Quality Assurance Module</p>
          </div>
          <span className="badge" style={{ background: hasAnyData ? '#10b981' : '#9ca3af' }}>
            {hasAnyData ? 'Ready to Commit' : 'Pending Triage'}
          </span>
        </div>

        <h4 style={{ marginTop: 24, color: 'var(--color-muted)', letterSpacing: 0.5, fontSize: 12 }}>
          ORIGIN, PRODUCT & COMPLAINT DETAILS
        </h4>
        <div className="field-grid">
          {Object.entries(FIELD_LABELS).map(([key, label]) => (
            <div key={key} className={fieldClass(key)} style={key === 'complaint_description' ? { gridColumn: '1 / -1' } : undefined}>
              <label>{label}</label>
              <div className={'copilot-field-value' + (fields[key] ? '' : ' empty')}>
                {fields[key] || 'Awaiting AI extraction…'}
              </div>
            </div>
          ))}
        </div>

        <h4 style={{ color: 'var(--color-muted)', letterSpacing: 0.5, fontSize: 12 }}>AI COPILOT RISK ASSESSMENT</h4>
        <div className="field-grid">
          {Object.entries(AI_FIELDS).map(([key, label]) => (
            <div key={key} className={fieldClass(key)} style={key === 'initial_risk_assessment' ? { gridColumn: '1 / -1' } : undefined}>
              <label>{label}</label>
              <div className={'copilot-field-value' + (fields[key] ? '' : ' empty')}>
                {fields[key] || 'Awaiting AI extraction…'}
              </div>
            </div>
          ))}
        </div>

        <button className="primary" onClick={handleSave} disabled={!hasAnyData || saving}>
          {saving ? 'Saving…' : '💾 Save Complaint'}
        </button>
      </div>

      <div className="card chat-panel">
        <h3 style={{ marginTop: 0 }}>✨ AI Complaint Intake Assistant</h3>

        <div
          className={'dropzone' + (dragOver ? ' drag-over' : '')}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          ⬆ Drag & drop a complaint PDF here, or click to browse
          <input
            ref={fileInputRef}
            type="file"
            accept="application/pdf"
            style={{ display: 'none' }}
            onChange={(e) => handleFile(e.target.files?.[0])}
          />
        </div>

        <div className="chat-log">
          {messages.map((m, i) => (
            <div key={i} className={`chat-bubble ${m.role}`}>{m.text}</div>
          ))}
          {busy && <div className="chat-bubble assistant">Analyzing and extracting details…</div>}
        </div>

        <div className="chat-input-row">
          <input
            placeholder="Paste complaint text or ask me anything…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            disabled={busy}
          />
          <button className="primary" onClick={handleSend} disabled={busy || !input.trim()}>Send</button>
        </div>
      </div>
    </div>
  )
}
