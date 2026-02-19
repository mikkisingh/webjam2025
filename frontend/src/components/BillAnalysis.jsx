import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { supabase } from '../lib/supabase'

function BillAnalysis({ billData, onRequestAuth, fromHistory = false }) {
  const { user } = useAuth()
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(fromHistory)
  const [saveError, setSaveError] = useState(null)

  const { structured_data, analysis_results, summary, complaint_email } = billData

  // Auto-save when user is already logged in when analysis completes
  useEffect(() => {
    if (user && !fromHistory && !saved) {
      saveToSupabase()
    }
  }, [user])

  const saveToSupabase = async () => {
    if (saving || saved) return
    setSaving(true)
    setSaveError(null)

    const { error } = await supabase.from('analyses').insert({
      user_id: user.id,
      overall_severity: analysis_results?.overall_severity || null,
      potential_savings: analysis_results?.potential_savings || 0,
      issues_count: analysis_results?.issues?.length || 0,
      structured_data,
      analysis_results,
      summary,
      complaint_email,
    })

    if (error) {
      setSaveError('Could not save — your results are still shown below.')
    } else {
      setSaved(true)
    }
    setSaving(false)
  }

  const getSeverityClass = (severity) => {
    const map = { low: 'severity-low', medium: 'severity-medium', high: 'severity-high' }
    return map[severity?.toLowerCase()] || 'severity-low'
  }

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text)
    alert('Copied to clipboard!')
  }

  return (
    <div className="bill-analysis">
      <div className="analysis-header-row">
        <h2>Analysis Results</h2>

        {!fromHistory && (
          <div className="save-status">
            {saving && <span className="save-chip saving">Saving...</span>}
            {saved && !saving && <span className="save-chip saved">Saved to history</span>}
            {!user && !saved && (
              <div className="save-prompt">
                <span>Save results & track disputes</span>
                <button
                  className="button primary"
                  style={{ padding: '8px 16px', fontSize: 14 }}
                  onClick={onRequestAuth}
                >
                  Sign up free
                </button>
              </div>
            )}
            {saveError && <span className="save-chip save-error">{saveError}</span>}
          </div>
        )}
      </div>

      {/* Summary */}
      <section className="analysis-section summary-section">
        <h3>Summary</h3>
        <p className="summary-text">{summary}</p>
      </section>

      {/* Bill Details */}
      <section className="analysis-section details-section">
        <h3>Bill Details</h3>
        <div className="details-grid">
          <div className="detail-item">
            <span className="detail-label">Patient</span>
            <span className="detail-value">{structured_data.patient_name}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Provider</span>
            <span className="detail-value">{structured_data.provider_name}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Date of Service</span>
            <span className="detail-value">{structured_data.date_of_service}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Insurance</span>
            <span className="detail-value">{structured_data.insurance_info}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Total Amount</span>
            <span className="detail-value total-amount">${structured_data.total?.toFixed(2) || '0.00'}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Patient Responsibility</span>
            <span className="detail-value patient-resp">${structured_data.patient_responsibility?.toFixed(2) || '0.00'}</span>
          </div>
        </div>
      </section>

      {/* Charges Table */}
      <section className="analysis-section charges-section">
        <h3>Charges Breakdown</h3>
        <div className="charges-table">
          <table>
            <thead>
              <tr>
                <th>Item / Service</th>
                <th>Code</th>
                <th>Cost</th>
              </tr>
            </thead>
            <tbody>
              {structured_data.charges?.map((charge, i) => (
                <tr key={i}>
                  <td>{charge.item}</td>
                  <td>{charge.code || 'N/A'}</td>
                  <td className="charge-cost">${charge.cost?.toFixed(2) || '0.00'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Issues */}
      <section className="analysis-section issues-section">
        <h3>
          Issues Detected
          <span className={`severity-badge ${getSeverityClass(analysis_results.overall_severity)}`}>
            {analysis_results.overall_severity?.toUpperCase() || 'NONE'}
          </span>
        </h3>

        {analysis_results.issues?.length > 0 ? (
          <div className="issues-list">
            {analysis_results.issues.map((issue, i) => (
              <div key={i} className={`issue-item ${getSeverityClass(issue.severity)}`}>
                <div className="issue-header">
                  <span className="issue-type">{issue.type}</span>
                  <span className={`issue-severity ${getSeverityClass(issue.severity)}`}>{issue.severity}</span>
                </div>
                <p className="issue-description">{issue.description}</p>
                {issue.item && <p className="issue-item-name">Affected: {issue.item}</p>}
              </div>
            ))}
          </div>
        ) : (
          <p className="no-issues">No issues detected. Your bill appears to be in order.</p>
        )}

        {analysis_results.potential_savings > 0 && (
          <div className="potential-savings">
            <h4>Potential Savings</h4>
            <p className="savings-amount">${analysis_results.potential_savings?.toFixed(2)}</p>
          </div>
        )}
      </section>

      {/* Recommendations */}
      {analysis_results.recommendations?.length > 0 && (
        <section className="analysis-section recommendations-section">
          <h3>Recommendations</h3>
          <ul className="recommendations-list">
            {analysis_results.recommendations.map((rec, i) => (
              <li key={i}>{rec}</li>
            ))}
          </ul>
        </section>
      )}

      {/* Dispute Email */}
      {complaint_email && (
        <section className="analysis-section email-section">
          <h3>Dispute Email Template</h3>
          <p className="email-hint">Copy this email and send it to your provider's billing department:</p>
          <div className="email-template">
            <pre>{complaint_email}</pre>
          </div>
          <button className="button primary" onClick={() => copyToClipboard(complaint_email)}>
            Copy Email Template
          </button>
        </section>
      )}
    </div>
  )
}

export default BillAnalysis
