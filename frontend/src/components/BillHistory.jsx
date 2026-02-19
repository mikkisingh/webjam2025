import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'
import { useAuth } from '../context/AuthContext'

const STATUS_LABELS = {
  none: { label: 'No dispute', cls: 'status-none' },
  submitted: { label: 'Dispute submitted', cls: 'status-submitted' },
  in_progress: { label: 'In progress', cls: 'status-progress' },
  resolved: { label: 'Resolved', cls: 'status-resolved' },
  rejected: { label: 'Rejected', cls: 'status-rejected' },
}

const SEVERITY_ICONS = { high: '🔴', medium: '🟡', low: '🟢' }

function BillHistory({ onBack, onViewAnalysis }) {
  const { user } = useAuth()
  const [analyses, setAnalyses] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [deletingId, setDeletingId] = useState(null)
  const [confirmDeleteId, setConfirmDeleteId] = useState(null)

  useEffect(() => {
    fetchAnalyses()
  }, [])

  const fetchAnalyses = async () => {
    setLoading(true)
    const { data, error } = await supabase
      .from('analyses')
      .select('*')
      .order('created_at', { ascending: false })

    if (error) {
      setError('Could not load history.')
    } else {
      setAnalyses(data || [])
    }
    setLoading(false)
  }

  const handleDeleteClick = (id, e) => {
    e.stopPropagation()
    setConfirmDeleteId(id)
  }

  const handleDeleteConfirm = async (id) => {
    setConfirmDeleteId(null)
    setDeletingId(id)
    const { error } = await supabase.from('analyses').delete().eq('id', id)
    if (!error) {
      setAnalyses(prev => prev.filter(a => a.id !== id))
    }
    setDeletingId(null)
  }

  const handleDisputeStatus = async (id, newStatus, e) => {
    e.stopPropagation()
    const { error } = await supabase
      .from('analyses')
      .update({ dispute_status: newStatus })
      .eq('id', id)
    if (!error) {
      setAnalyses(prev => prev.map(a => a.id === id ? { ...a, dispute_status: newStatus } : a))
    }
  }

  const totalSavings = analyses
    .filter(a => a.dispute_status === 'resolved')
    .reduce((sum, a) => sum + (a.potential_savings || 0), 0)

  const formatDate = (iso) =>
    new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })

  return (
    <div className="section">
      <div className="container">
        <div className="history-header">
          <button className="button ghost" onClick={onBack}>← Back</button>
          <h2 style={{ margin: 0 }}>Your Bill History</h2>
          <div />
        </div>

        {/* Summary bar */}
        {analyses.length > 0 && (
          <div className="history-summary">
            <div className="history-stat">
              <span className="history-stat-value">{analyses.length}</span>
              <span className="history-stat-label">Bills analyzed</span>
            </div>
            <div className="history-stat">
              <span className="history-stat-value">
                ${analyses.reduce((s, a) => s + (a.potential_savings || 0), 0).toFixed(0)}
              </span>
              <span className="history-stat-label">Potential savings found</span>
            </div>
            <div className="history-stat">
              <span className="history-stat-value" style={{ color: 'var(--brand)' }}>
                ${totalSavings.toFixed(0)}
              </span>
              <span className="history-stat-label">Confirmed savings</span>
            </div>
          </div>
        )}

        {loading && (
          <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--muted)' }}>
            Loading your history...
          </div>
        )}

        {error && <div className="error-message">{error}</div>}

        {!loading && !error && analyses.length === 0 && (
          <div className="history-empty">
            <div style={{ fontSize: 48, marginBottom: 16 }}>📋</div>
            <h3>No analyses yet</h3>
            <p>Upload a medical bill to get started. Sign in to save your results here.</p>
            <button className="button primary" onClick={onBack}>Analyze a bill</button>
          </div>
        )}

        {!loading && analyses.length > 0 && (
          <div className="history-list">
            {analyses.map(analysis => {
              const status = STATUS_LABELS[analysis.dispute_status] || STATUS_LABELS.none
              const providerName = analysis.structured_data?.provider_name || 'Unknown provider'
              const patientName = analysis.structured_data?.patient_name || ''
              const total = analysis.structured_data?.total

              return (
                <div
                  key={analysis.id}
                  className="history-item"
                  onClick={() => onViewAnalysis(analysis)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={e => e.key === 'Enter' && onViewAnalysis(analysis)}
                >
                  <div className="history-item-left">
                    <span className="history-severity-icon">
                      {SEVERITY_ICONS[analysis.overall_severity] || '⚪'}
                    </span>
                  </div>

                  <div className="history-item-info">
                    <div className="history-item-title">
                      {providerName}
                      {patientName && <span className="history-item-patient"> · {patientName}</span>}
                    </div>
                    <div className="history-item-meta">
                      <span>{formatDate(analysis.created_at)}</span>
                      {analysis.issues_count > 0 && (
                        <span className="history-issues-count">
                          {analysis.issues_count} issue{analysis.issues_count !== 1 ? 's' : ''} found
                        </span>
                      )}
                      {analysis.potential_savings > 0 && (
                        <span className="history-savings">
                          ${analysis.potential_savings?.toFixed(0)} potential savings
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="history-item-right">
                    {total && (
                      <span className="history-total">${total.toFixed(2)}</span>
                    )}
                    <select
                      className={`dispute-select ${status.cls}`}
                      value={analysis.dispute_status || 'none'}
                      onChange={e => handleDisputeStatus(analysis.id, e.target.value, e)}
                      onClick={e => e.stopPropagation()}
                    >
                      <option value="none">No dispute</option>
                      <option value="submitted">Submitted</option>
                      <option value="in_progress">In progress</option>
                      <option value="resolved">Resolved</option>
                      <option value="rejected">Rejected</option>
                    </select>
                    {confirmDeleteId === analysis.id ? (
                      <span className="history-confirm-delete" onClick={e => e.stopPropagation()}>
                        <button
                          className="button ghost"
                          style={{ fontSize: 12, padding: '4px 8px' }}
                          onClick={() => setConfirmDeleteId(null)}
                        >
                          Cancel
                        </button>
                        <button
                          className="button ghost"
                          style={{ fontSize: 12, padding: '4px 8px', color: '#e53935' }}
                          onClick={() => handleDeleteConfirm(analysis.id)}
                        >
                          Delete
                        </button>
                      </span>
                    ) : (
                      <button
                        className="history-delete-btn"
                        onClick={e => handleDeleteClick(analysis.id, e)}
                        disabled={deletingId === analysis.id}
                        aria-label="Delete analysis"
                      >
                        {deletingId === analysis.id ? '...' : '✕'}
                      </button>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

export default BillHistory
