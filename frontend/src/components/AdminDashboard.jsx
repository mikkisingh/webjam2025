import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'
import { useAuth } from '../context/AuthContext'
import { API_URL } from '../lib/api'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, Cell, ResponsiveContainer
} from 'recharts'

const SEVERITY_COLORS = { high: '#e53935', medium: '#fb8c00', low: '#43a047' }
const DISPUTE_COLORS  = {
  none: 'var(--muted)',
  submitted: '#1e88e5',
  in_progress: '#fb8c00',
  resolved: '#43a047',
  rejected: '#e53935',
}
const DISPUTE_LABELS = {
  none: 'No dispute',
  submitted: 'Submitted',
  in_progress: 'In progress',
  resolved: 'Resolved',
  rejected: 'Rejected',
}

function StatCard({ value, label, prefix = '', format = 'number' }) {
  const display = format === 'currency'
    ? `${prefix}${Number(value).toLocaleString(undefined, { maximumFractionDigits: 0 })}`
    : `${prefix}${Number(value).toLocaleString()}`
  return (
    <div className="admin-card">
      <div className="admin-card-value">{display}</div>
      <div className="admin-card-label">{label}</div>
    </div>
  )
}

function AdminDashboard({ onBack }) {
  const { user } = useAuth()
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Admin promote state
  const [promoteEmail, setPromoteEmail] = useState('')
  const [promoting, setPromoting] = useState(false)
  const [promoteResult, setPromoteResult] = useState(null)

  useEffect(() => {
    const fetchStats = async () => {
      const { data, error } = await supabase.rpc('get_admin_stats')
      if (error) {
        setError('Failed to load statistics. Make sure the admin functions are deployed in Supabase.')
      } else {
        setStats(data)
      }
      setLoading(false)
    }
    fetchStats()
  }, [])

  const handlePromote = async (e) => {
    e.preventDefault()
    const email = promoteEmail.trim()
    if (!email) return

    setPromoting(true)
    setPromoteResult(null)

    try {
      const { data: { session } } = await supabase.auth.getSession()
      const jwt = session?.access_token
      if (!jwt) throw new Error('Not authenticated')

      const resp = await fetch(`${API_URL}/admin/promote`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${jwt}`,
        },
        body: JSON.stringify({ email }),
      })

      const result = await resp.json()
      if (!resp.ok) throw new Error(result.error || 'Promotion failed')

      setPromoteResult({ ok: true, message: `${email} is now an admin.` })
      setPromoteEmail('')
    } catch (err) {
      setPromoteResult({ ok: false, message: err.message })
    } finally {
      setPromoting(false)
    }
  }

  const severityData = stats?.severity_breakdown
    ? Object.entries(stats.severity_breakdown)
        .map(([name, value]) => ({ name: name.charAt(0).toUpperCase() + name.slice(1), value, key: name }))
        .sort((a, b) => ['high', 'medium', 'low'].indexOf(a.key) - ['high', 'medium', 'low'].indexOf(b.key))
    : []

  const disputeData = stats?.dispute_breakdown
    ? Object.entries(stats.dispute_breakdown)
        .map(([name, value]) => ({ name: DISPUTE_LABELS[name] || name, value, key: name }))
        .sort((a, b) => Object.keys(DISPUTE_LABELS).indexOf(a.key) - Object.keys(DISPUTE_LABELS).indexOf(b.key))
    : []

  return (
    <div className="section">
      <div className="container">

        <div className="history-header">
          <button className="button ghost" onClick={onBack}>← Back</button>
          <h2 style={{ margin: 0 }}>Admin Dashboard</h2>
          <div />
        </div>

        {loading && (
          <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--muted)' }}>
            Loading statistics...
          </div>
        )}

        {error && <div className="error-message" style={{ marginTop: 24 }}>{error}</div>}

        {!loading && stats && (
          <>
            {/* ── Overview cards ── */}
            <h3 className="admin-section-title">Overview</h3>
            <div className="admin-grid">
              <StatCard value={stats.total_analyses}          label="Bills analyzed" />
              <StatCard value={stats.active_users}            label="Active users" />
              <StatCard value={stats.total_potential_savings} label="Potential savings identified" prefix="$" format="currency" />
              <StatCard value={stats.total_confirmed_savings} label="Confirmed savings (resolved)" prefix="$" format="currency" />
              <StatCard value={stats.last_7_days}             label="New this week" />
              <StatCard value={stats.last_30_days}            label="New this month" />
            </div>

            {/* ── Charts ── */}
            {(severityData.length > 0 || disputeData.length > 0) && (
              <>
                <h3 className="admin-section-title">Breakdowns</h3>
                <div className="admin-charts">

                  {severityData.length > 0 && (
                    <div className="admin-chart-section">
                      <div className="admin-chart-title">Severity</div>
                      <ResponsiveContainer width="100%" height={180}>
                        <BarChart data={severityData} layout="vertical" margin={{ left: 8, right: 24, top: 4, bottom: 4 }}>
                          <XAxis type="number" tick={{ fill: 'var(--muted)', fontSize: 12 }} axisLine={false} tickLine={false} />
                          <YAxis type="category" dataKey="name" tick={{ fill: 'var(--text)', fontSize: 13 }} width={64} axisLine={false} tickLine={false} />
                          <Tooltip
                            contentStyle={{ background: 'var(--panel)', border: '1px solid var(--card-border)', borderRadius: 8, color: 'var(--text)' }}
                            cursor={{ fill: 'var(--panel-alt)' }}
                          />
                          <Bar dataKey="value" radius={[0, 4, 4, 0]} maxBarSize={28}>
                            {severityData.map(entry => (
                              <Cell key={entry.key} fill={SEVERITY_COLORS[entry.key] || 'var(--brand)'} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  )}

                  {disputeData.length > 0 && (
                    <div className="admin-chart-section">
                      <div className="admin-chart-title">Dispute outcomes</div>
                      <ResponsiveContainer width="100%" height={240}>
                        <BarChart data={disputeData} layout="vertical" margin={{ left: 8, right: 24, top: 4, bottom: 4 }}>
                          <XAxis type="number" tick={{ fill: 'var(--muted)', fontSize: 12 }} axisLine={false} tickLine={false} />
                          <YAxis type="category" dataKey="name" tick={{ fill: 'var(--text)', fontSize: 13 }} width={80} axisLine={false} tickLine={false} />
                          <Tooltip
                            contentStyle={{ background: 'var(--panel)', border: '1px solid var(--card-border)', borderRadius: 8, color: 'var(--text)' }}
                            cursor={{ fill: 'var(--panel-alt)' }}
                          />
                          <Bar dataKey="value" radius={[0, 4, 4, 0]} maxBarSize={28}>
                            {disputeData.map(entry => (
                              <Cell key={entry.key} fill={DISPUTE_COLORS[entry.key] || 'var(--brand)'} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  )}

                </div>
              </>
            )}

            {/* ── Admin management ── */}
            <h3 className="admin-section-title">Admin Management</h3>
            <div className="admin-promote">
              <p style={{ color: 'var(--muted)', marginBottom: 16, fontSize: 14 }}>
                Grant admin access to another user by their registered email address.
              </p>
              <form className="admin-promote-form" onSubmit={handlePromote}>
                <input
                  className="admin-promote-input"
                  type="email"
                  placeholder="user@example.com"
                  value={promoteEmail}
                  onChange={e => setPromoteEmail(e.target.value)}
                  required
                />
                <button className="button primary" type="submit" disabled={promoting}>
                  {promoting ? 'Granting…' : 'Grant admin'}
                </button>
              </form>
              {promoteResult && (
                <div className={`admin-promote-result ${promoteResult.ok ? 'ok' : 'err'}`}>
                  {promoteResult.message}
                </div>
              )}
            </div>

          </>
        )}

      </div>
    </div>
  )
}

export default AdminDashboard
