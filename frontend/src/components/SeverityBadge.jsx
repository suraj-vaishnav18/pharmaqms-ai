const COLORS = {
  low: 'var(--severity-low)',
  medium: 'var(--severity-medium)',
  high: 'var(--severity-high)',
  critical: 'var(--severity-critical)',
}

export default function SeverityBadge({ severity }) {
  if (!severity) return <span className="badge" style={{ background: '#9ca3af' }}>unclassified</span>
  return (
    <span className="badge" style={{ background: COLORS[severity] || '#9ca3af' }}>
      {severity}
    </span>
  )
}
