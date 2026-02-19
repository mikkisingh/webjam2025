import { useState, useEffect, useRef } from 'react'
import { API_URL } from '../lib/api'

const fmt = (n) =>
  n != null ? `$${Number(n).toLocaleString(undefined, { maximumFractionDigits: 2 })}` : '—'

const fmtInt = (n) =>
  n != null ? Number(n).toLocaleString() : '—'

const TABS = [
  { id: 'cpt',   label: 'CPT / Medicare',       icon: '💊', endpoint: '/procedures/search' },
  { id: 'hcpcs', label: 'HCPCS Supplies',       icon: '🩹', endpoint: '/hcpcs/search' },
  { id: 'icd10', label: 'ICD-10 Procedures',    icon: '🏥', endpoint: '/icd10/search' },
]

export default function PriceExplorer() {
  const [activeTab, setActiveTab]   = useState('cpt')
  const [query, setQuery]           = useState('')
  const [category, setCategory]     = useState('All')
  const [categories, setCategories] = useState([])
  const [results, setResults]       = useState(null)
  const [loading, setLoading]       = useState(false)
  const [error, setError]           = useState(null)
  const [expanded, setExpanded]     = useState(null)
  const inputRef                    = useRef(null)

  useEffect(() => {
    const catEndpoint =
      activeTab === 'cpt' ? '/procedures/categories'
      : activeTab === 'hcpcs' ? '/hcpcs/categories'
      : null

    if (catEndpoint) {
      fetch(`${API_URL}${catEndpoint}`)
        .then((r) => r.json())
        .then((data) => setCategories(data.categories || []))
        .catch(() => setCategories([]))
    } else {
      setCategories([])
    }
  }, [activeTab])

  useEffect(() => {
    doSearch('', 'Evaluation & Management', 'cpt')
  }, [])

  const doSearch = async (q, cat, tabId) => {
    const t = TABS.find((x) => x.id === (tabId || activeTab))
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams({ limit: 50 })
      if (q) params.set('q', q)
      if (cat && cat !== 'All' && t.id !== 'icd10') params.set('category', cat)

      const res = await fetch(`${API_URL}${t.endpoint}?${params}`)
      if (!res.ok) throw new Error(`Server error ${res.status}`)
      const data = await res.json()
      setResults(data.results)
    } catch (err) {
      setError(err.message)
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    doSearch(query, category)
  }

  const handleTabChange = (tabId) => {
    setActiveTab(tabId)
    setResults(null)
    setExpanded(null)
    setCategory('All')
    setQuery('')
  }

  const handleCategoryChange = (cat) => {
    setCategory(cat)
    doSearch(query, cat)
  }

  const toggleRow = (code) =>
    setExpanded((prev) => (prev === code ? null : code))

  const placeholders = {
    cpt: 'Search by procedure name or CPT code (e.g. MRI, 99213, colonoscopy)',
    hcpcs: 'Search HCPCS codes (e.g. wheelchair, insulin, E0950)',
    icd10: 'Search ICD-10-PCS codes (e.g. appendix, bypass, knee)',
  }

  return (
    <div className="pe">
      {/* ── Tab bar ── */}
      <div className="pe-tabs" role="tablist">
        {TABS.map((t) => (
          <button
            key={t.id}
            role="tab"
            aria-selected={activeTab === t.id}
            className={`pe-tab ${activeTab === t.id ? 'pe-tab--active' : ''}`}
            onClick={() => handleTabChange(t.id)}
          >
            <span className="pe-tab-icon">{t.icon}</span>
            <span className="pe-tab-label">{t.label}</span>
          </button>
        ))}
      </div>

      {/* ── Search + Category ── */}
      <div className="pe-controls">
        <form className="pe-search-form" onSubmit={handleSubmit}>
          <div className="pe-search-wrap">
            <svg className="pe-search-icon" viewBox="0 0 20 20" fill="currentColor" width="18" height="18">
              <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd"/>
            </svg>
            <input
              ref={inputRef}
              type="text"
              className="pe-search-input"
              placeholder={placeholders[activeTab]}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              aria-label="Search procedures"
            />
          </div>
          {categories.length > 0 && (
            <select
              className="pe-cat-select"
              value={category}
              onChange={(e) => handleCategoryChange(e.target.value)}
              aria-label="Filter by category"
            >
              <option value="All">All categories</option>
              {categories.map((cat) => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          )}
          <button className="button primary pe-search-btn" type="submit" disabled={loading}>
            {loading ? 'Searching...' : 'Search'}
          </button>
        </form>
      </div>

      {/* ── Error ── */}
      {error && (
        <p className="pe-error">
          Could not load data — make sure the backend is running.
        </p>
      )}

      {/* ── Results ── */}
      {results !== null && !error && (
        <>
          <div className="pe-results-header">
            <span className="pe-result-count">
              {results.length === 0
                ? 'No results found'
                : `${results.length} procedure${results.length !== 1 ? 's' : ''}`}
            </span>
            {category !== 'All' && (
              <span className="pe-active-filter">
                {category}
                <button className="pe-clear-filter" onClick={() => handleCategoryChange('All')}>✕</button>
              </span>
            )}
          </div>

          {results.length > 0 && activeTab === 'cpt' && (
            <div className="pe-cards">
              {results.map((p) => (
                <CptCard key={p.cpt_code} p={p} expanded={expanded === p.cpt_code} onToggle={() => toggleRow(p.cpt_code)} />
              ))}
            </div>
          )}
          {results.length > 0 && activeTab === 'hcpcs' && (
            <div className="pe-cards">
              {results.map((h) => (
                <HcpcsCard key={h.hcpcs_code} h={h} />
              ))}
            </div>
          )}
          {results.length > 0 && activeTab === 'icd10' && (
            <div className="pe-cards">
              {results.map((i) => (
                <Icd10Card key={i.icd10_code} i={i} />
              ))}
            </div>
          )}
        </>
      )}

      {results === null && !loading && !error && (
        <p className="muted" style={{ textAlign: 'center', padding: '3rem 0' }}>
          Search above to look up procedure codes and pricing.
        </p>
      )}
    </div>
  )
}


/* ─────────────── CPT Card ─────────────── */
function CptCard({ p, expanded, onToggle }) {
  const hasPrice = p.medicare_rate != null
  const markupRatio = hasPrice && p.typical_high ? (p.typical_high / p.medicare_rate).toFixed(1) : null

  return (
    <div className={`pe-card ${expanded ? 'pe-card--expanded' : ''}`}>
      <div className="pe-card-main" onClick={onToggle}>
        <div className="pe-card-left">
          <span className="pe-code">{p.cpt_code}</span>
          <span className="pe-card-cat">{p.category}</span>
        </div>
        <div className="pe-card-center">
          <span className="pe-card-name">{p.description}</span>
        </div>
        <div className="pe-card-prices">
          {hasPrice ? (
            <>
              <div className="pe-price-block">
                <span className="pe-price-label">Medicare</span>
                <span className="pe-price-value pe-price-medicare">{fmt(p.medicare_rate)}</span>
              </div>
              <div className="pe-price-block">
                <span className="pe-price-label">Typical Range</span>
                <span className="pe-price-value">{fmt(p.typical_low)} – <span className="pe-price-high">{fmt(p.typical_high)}</span></span>
              </div>
            </>
          ) : (
            <span className="pe-no-price">No pricing data</span>
          )}
        </div>
        <div className="pe-card-chevron">{expanded ? '▾' : '▸'}</div>
      </div>

      {expanded && (
        <div className="pe-card-detail">
          {/* Fee comparison */}
          <div className="pe-fee-row">
            <div className="pe-fee-item">
              <span className="pe-fee-label">Non-Facility Fee</span>
              <span className="pe-fee-value">{fmt(p.non_fac_fee)}</span>
              <span className="pe-fee-note">Office / clinic</span>
            </div>
            <div className="pe-fee-item">
              <span className="pe-fee-label">Facility Fee</span>
              <span className="pe-fee-value">{fmt(p.fac_fee)}</span>
              <span className="pe-fee-note">Hospital / ASC</span>
            </div>
            <div className="pe-fee-item">
              <span className="pe-fee-label">Cash Price Range</span>
              <span className="pe-fee-value">{fmt(p.typical_low)} – {fmt(p.typical_high)}</span>
              <span className="pe-fee-note">Estimated uninsured</span>
            </div>
            {markupRatio && (
              <div className="pe-fee-item">
                <span className="pe-fee-label">Markup</span>
                <span className="pe-fee-value pe-markup">{markupRatio}×</span>
                <span className="pe-fee-note">vs Medicare</span>
              </div>
            )}
          </div>

          {/* Price visualization bar */}
          {hasPrice && p.typical_high > 0 && (
            <div className="pe-price-bar-wrap">
              <div className="pe-price-bar">
                <div
                  className="pe-price-bar-medicare"
                  style={{ width: `${Math.min((p.medicare_rate / p.typical_high) * 100, 100)}%` }}
                >
                  <span>Medicare {fmt(p.medicare_rate)}</span>
                </div>
                <div
                  className="pe-price-bar-typical"
                  style={{ width: `${Math.min(((p.typical_low - p.medicare_rate) / p.typical_high) * 100, 60)}%` }}
                />
                <div
                  className="pe-price-bar-high"
                  style={{ flex: 1 }}
                >
                  <span>{fmt(p.typical_high)}</span>
                </div>
              </div>
              <div className="pe-price-bar-labels">
                <span>Lowest</span>
                <span>Highest</span>
              </div>
            </div>
          )}

          {/* RVU breakdown */}
          {p.work_rvu != null && (
            <details className="pe-details-block">
              <summary className="pe-details-summary">RVU Breakdown</summary>
              <div className="pe-rvu-grid">
                <div className="pe-rvu-item"><span className="pe-rvu-label">Work RVU</span><span className="pe-rvu-value">{p.work_rvu}</span></div>
                <div className="pe-rvu-item"><span className="pe-rvu-label">PE (Non-Fac)</span><span className="pe-rvu-value">{p.non_fac_pe_rvu ?? '—'}</span></div>
                <div className="pe-rvu-item"><span className="pe-rvu-label">PE (Facility)</span><span className="pe-rvu-value">{p.fac_pe_rvu ?? '—'}</span></div>
                <div className="pe-rvu-item"><span className="pe-rvu-label">MP RVU</span><span className="pe-rvu-value">{p.mp_rvu ?? '—'}</span></div>
                <div className="pe-rvu-item"><span className="pe-rvu-label">Total (Non-Fac)</span><span className="pe-rvu-value pe-rvu-total">{p.total_non_fac_rvu ?? '—'}</span></div>
                <div className="pe-rvu-item"><span className="pe-rvu-label">Total (Facility)</span><span className="pe-rvu-value pe-rvu-total">{p.total_fac_rvu ?? '—'}</span></div>
                <div className="pe-rvu-item"><span className="pe-rvu-label">Conv. Factor</span><span className="pe-rvu-value">{p.conversion_factor ? `$${p.conversion_factor}` : '—'}</span></div>
                <div className="pe-rvu-item"><span className="pe-rvu-label">Global Period</span><span className="pe-rvu-value">{p.global_period || '—'}</span></div>
              </div>
            </details>
          )}

          {p.utilization && (
            <details className="pe-details-block">
              <summary className="pe-details-summary">Medicare Utilization Stats</summary>
              <div className="pe-rvu-grid">
                <div className="pe-rvu-item"><span className="pe-rvu-label">Avg Submitted</span><span className="pe-rvu-value">{fmt(p.utilization.avg_submitted_charge)}</span></div>
                <div className="pe-rvu-item"><span className="pe-rvu-label">Avg Allowed</span><span className="pe-rvu-value">{fmt(p.utilization.avg_allowed_amount)}</span></div>
                <div className="pe-rvu-item"><span className="pe-rvu-label">Avg Payment</span><span className="pe-rvu-value">{fmt(p.utilization.avg_medicare_payment)}</span></div>
                <div className="pe-rvu-item"><span className="pe-rvu-label">Providers</span><span className="pe-rvu-value">{fmtInt(p.utilization.total_providers)}</span></div>
                <div className="pe-rvu-item"><span className="pe-rvu-label">Total Services</span><span className="pe-rvu-value">{fmtInt(p.utilization.total_services)}</span></div>
                <div className="pe-rvu-item"><span className="pe-rvu-label">Beneficiaries</span><span className="pe-rvu-value">{fmtInt(p.utilization.total_beneficiaries)}</span></div>
              </div>
            </details>
          )}

          <p className="pe-disclaimer">
            Source: CMS Medicare Physician Fee Schedule {p.source_year || 2026}. Actual charges vary by location and provider.
          </p>
        </div>
      )}
    </div>
  )
}


/* ─────────────── HCPCS Card ─────────────── */
function HcpcsCard({ h }) {
  return (
    <div className="pe-card pe-card--simple">
      <div className="pe-card-left">
        <span className="pe-code">{h.hcpcs_code}</span>
        <span className="pe-card-cat">{h.category}</span>
      </div>
      <div className="pe-card-center">
        <span className="pe-card-name">{h.short_desc}</span>
        {h.long_desc && h.long_desc !== h.short_desc && (
          <span className="pe-card-desc">{h.long_desc}</span>
        )}
      </div>
    </div>
  )
}


/* ─────────────── ICD-10 Card ─────────────── */
function Icd10Card({ i }) {
  return (
    <div className="pe-card pe-card--simple">
      <div className="pe-card-left">
        <span className="pe-code">{i.icd10_code}</span>
      </div>
      <div className="pe-card-center">
        <span className="pe-card-name">{i.short_desc}</span>
        {i.long_desc && i.long_desc !== i.short_desc && (
          <span className="pe-card-desc">{i.long_desc}</span>
        )}
      </div>
    </div>
  )
}
