import { useState, useEffect, useRef } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001'

const fmt = (n) =>
  n != null ? `$${Number(n).toLocaleString(undefined, { maximumFractionDigits: 2 })}` : '—'

const fmtInt = (n) =>
  n != null ? Number(n).toLocaleString() : '—'

const TABS = [
  { id: 'cpt',   label: 'CPT / Medicare',     endpoint: '/procedures/search', codeField: 'cpt_code' },
  { id: 'hcpcs', label: 'HCPCS (Supplies/DME)', endpoint: '/hcpcs/search',     codeField: 'hcpcs_code' },
  { id: 'icd10', label: 'ICD-10 (Inpatient)',   endpoint: '/icd10/search',      codeField: 'icd10_code' },
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

  const tab = TABS.find((t) => t.id === activeTab)

  // Fetch categories dynamically when tab changes
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

  // Auto-load on first render
  useEffect(() => {
    doSearch('', 'Evaluation & Management', 'cpt')
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

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
    <div className="price-explorer">
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
            {t.label}
          </button>
        ))}
      </div>

      {/* ── Search bar ── */}
      <form className="pe-search-form" onSubmit={handleSubmit}>
        <input
          ref={inputRef}
          type="text"
          className="pe-search-input"
          placeholder={placeholders[activeTab]}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          aria-label="Search procedures"
        />
        <button className="button primary" type="submit" disabled={loading}>
          {loading ? 'Searching…' : 'Search'}
        </button>
      </form>

      {/* ── Category pills (CPT and HCPCS only) ── */}
      {categories.length > 0 && (
        <div className="pe-categories" role="group" aria-label="Filter by category">
          <button
            type="button"
            className={`pe-pill ${category === 'All' ? 'pe-pill--active' : ''}`}
            onClick={() => handleCategoryChange('All')}
          >
            All
          </button>
          {categories.map((cat) => (
            <button
              key={cat}
              type="button"
              className={`pe-pill ${category === cat ? 'pe-pill--active' : ''}`}
              onClick={() => handleCategoryChange(cat)}
            >
              {cat}
            </button>
          ))}
        </div>
      )}

      {/* ── Error ── */}
      {error && (
        <p className="pe-error">
          Could not load data — make sure the backend is running.
        </p>
      )}

      {/* ── Results ── */}
      {results !== null && !error && (
        <>
          <p className="pe-result-count muted">
            {results.length === 0
              ? 'No results found.'
              : `${results.length} result${results.length !== 1 ? 's' : ''} found`}
          </p>

          {results.length > 0 && activeTab === 'cpt' && (
            <CptTable results={results} expanded={expanded} toggleRow={toggleRow} />
          )}
          {results.length > 0 && activeTab === 'hcpcs' && (
            <HcpcsTable results={results} />
          )}
          {results.length > 0 && activeTab === 'icd10' && (
            <Icd10Table results={results} />
          )}
        </>
      )}

      {results === null && !loading && !error && (
        <p className="muted" style={{ textAlign: 'center', padding: '2rem 0' }}>
          Enter a search term above to look up procedure codes and pricing.
        </p>
      )}
    </div>
  )
}


/* ─────────────── CPT / Medicare Table ─────────────── */
function CptTable({ results, expanded, toggleRow }) {
  return (
    <div className="pe-table-wrap">
      <table className="pe-table">
        <thead>
          <tr>
            <th>CPT Code</th>
            <th>Procedure</th>
            <th>Category</th>
            <th className="pe-num">Medicare Rate</th>
            <th className="pe-num">Typical Low</th>
            <th className="pe-num">Typical High</th>
          </tr>
        </thead>
        <tbody>
          {results.map((p) => (
            <CptRow key={p.cpt_code} p={p} expanded={expanded} toggleRow={toggleRow} />
          ))}
        </tbody>
      </table>
    </div>
  )
}

function CptRow({ p, expanded, toggleRow }) {
  const isExpanded = expanded === p.cpt_code

  return (
    <>
      <tr
        className={`pe-row ${isExpanded ? 'pe-row--expanded' : ''}`}
        onClick={() => toggleRow(p.cpt_code)}
        style={{ cursor: 'pointer' }}
      >
        <td><span className="pe-code">{p.cpt_code}</span></td>
        <td className="pe-desc">{p.description}</td>
        <td><span className="pe-category-tag">{p.category}</span></td>
        <td className="pe-num pe-medicare">{fmt(p.medicare_rate)}</td>
        <td className="pe-num">{fmt(p.typical_low)}</td>
        <td className="pe-num pe-high">{fmt(p.typical_high)}</td>
      </tr>

      {isExpanded && (
        <tr className="pe-detail-row">
          <td colSpan={6}>
            <div className="pe-detail">
              {/* Pricing row */}
              <div className="pe-detail-grid">
                <div className="pe-detail-item">
                  <span className="pe-detail-label">Non-Facility Fee</span>
                  <span className="pe-detail-value pe-medicare">{fmt(p.non_fac_fee)}</span>
                  <span className="pe-detail-note">Office / clinic setting</span>
                </div>
                <div className="pe-detail-item">
                  <span className="pe-detail-label">Facility Fee</span>
                  <span className="pe-detail-value">{fmt(p.fac_fee)}</span>
                  <span className="pe-detail-note">Hospital / ASC setting</span>
                </div>
                <div className="pe-detail-item">
                  <span className="pe-detail-label">Typical Cash Price</span>
                  <span className="pe-detail-value">
                    {fmt(p.typical_low)} – {fmt(p.typical_high)}
                  </span>
                  <span className="pe-detail-note">Estimated range for uninsured patients</span>
                </div>
                <div className="pe-detail-item">
                  <span className="pe-detail-label">Markup Ratio</span>
                  <span className="pe-detail-value">
                    {p.medicare_rate
                      ? `${(p.typical_high / p.medicare_rate).toFixed(1)}×`
                      : '—'}
                  </span>
                  <span className="pe-detail-note">High-end vs Medicare</span>
                </div>
              </div>

              {/* RVU breakdown */}
              {p.work_rvu != null && (
                <div className="pe-rvu-section">
                  <h4 className="pe-section-title">RVU Breakdown</h4>
                  <div className="pe-rvu-grid">
                    <div className="pe-rvu-item">
                      <span className="pe-rvu-label">Work RVU</span>
                      <span className="pe-rvu-value">{p.work_rvu}</span>
                    </div>
                    <div className="pe-rvu-item">
                      <span className="pe-rvu-label">PE RVU (Non-Fac)</span>
                      <span className="pe-rvu-value">{p.non_fac_pe_rvu ?? '—'}</span>
                    </div>
                    <div className="pe-rvu-item">
                      <span className="pe-rvu-label">PE RVU (Facility)</span>
                      <span className="pe-rvu-value">{p.fac_pe_rvu ?? '—'}</span>
                    </div>
                    <div className="pe-rvu-item">
                      <span className="pe-rvu-label">MP RVU</span>
                      <span className="pe-rvu-value">{p.mp_rvu ?? '—'}</span>
                    </div>
                    <div className="pe-rvu-item">
                      <span className="pe-rvu-label">Total (Non-Fac)</span>
                      <span className="pe-rvu-value pe-rvu-total">{p.total_non_fac_rvu ?? '—'}</span>
                    </div>
                    <div className="pe-rvu-item">
                      <span className="pe-rvu-label">Total (Facility)</span>
                      <span className="pe-rvu-value pe-rvu-total">{p.total_fac_rvu ?? '—'}</span>
                    </div>
                    <div className="pe-rvu-item">
                      <span className="pe-rvu-label">Conv. Factor</span>
                      <span className="pe-rvu-value">{p.conversion_factor ? `$${p.conversion_factor}` : '—'}</span>
                    </div>
                    <div className="pe-rvu-item">
                      <span className="pe-rvu-label">Global Period</span>
                      <span className="pe-rvu-value">{p.global_period || '—'}</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Utilization stats (if available) */}
              {p.utilization && (
                <div className="pe-util-section">
                  <h4 className="pe-section-title">Medicare Utilization Stats</h4>
                  <div className="pe-rvu-grid">
                    <div className="pe-rvu-item">
                      <span className="pe-rvu-label">Avg Submitted</span>
                      <span className="pe-rvu-value">{fmt(p.utilization.avg_submitted_charge)}</span>
                    </div>
                    <div className="pe-rvu-item">
                      <span className="pe-rvu-label">Avg Allowed</span>
                      <span className="pe-rvu-value">{fmt(p.utilization.avg_allowed_amount)}</span>
                    </div>
                    <div className="pe-rvu-item">
                      <span className="pe-rvu-label">Avg Payment</span>
                      <span className="pe-rvu-value">{fmt(p.utilization.avg_medicare_payment)}</span>
                    </div>
                    <div className="pe-rvu-item">
                      <span className="pe-rvu-label">Providers</span>
                      <span className="pe-rvu-value">{fmtInt(p.utilization.total_providers)}</span>
                    </div>
                    <div className="pe-rvu-item">
                      <span className="pe-rvu-label">Total Services</span>
                      <span className="pe-rvu-value">{fmtInt(p.utilization.total_services)}</span>
                    </div>
                    <div className="pe-rvu-item">
                      <span className="pe-rvu-label">Beneficiaries</span>
                      <span className="pe-rvu-value">{fmtInt(p.utilization.total_beneficiaries)}</span>
                    </div>
                  </div>
                </div>
              )}

              <p className="pe-disclaimer">
                Source: CMS Medicare Physician Fee Schedule {p.source_year || 2026}. Fees computed from
                Total RVU × Conversion Factor (${p.conversion_factor || '33.40'}). Actual charges vary
                by location, provider, and facility type.
              </p>
            </div>
          </td>
        </tr>
      )}
    </>
  )
}


/* ─────────────── HCPCS Table ─────────────── */
function HcpcsTable({ results }) {
  return (
    <div className="pe-table-wrap">
      <table className="pe-table">
        <thead>
          <tr>
            <th>HCPCS Code</th>
            <th>Short Description</th>
            <th>Long Description</th>
            <th>Category</th>
          </tr>
        </thead>
        <tbody>
          {results.map((h) => (
            <tr key={h.hcpcs_code} className="pe-row">
              <td><span className="pe-code">{h.hcpcs_code}</span></td>
              <td className="pe-desc">{h.short_desc}</td>
              <td className="pe-desc">{h.long_desc}</td>
              <td><span className="pe-category-tag">{h.category}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}


/* ─────────────── ICD-10 Table ─────────────── */
function Icd10Table({ results }) {
  return (
    <div className="pe-table-wrap">
      <table className="pe-table">
        <thead>
          <tr>
            <th>ICD-10 Code</th>
            <th>Short Description</th>
            <th>Long Description</th>
          </tr>
        </thead>
        <tbody>
          {results.map((i) => (
            <tr key={i.icd10_code} className="pe-row">
              <td><span className="pe-code">{i.icd10_code}</span></td>
              <td className="pe-desc">{i.short_desc}</td>
              <td className="pe-desc">{i.long_desc}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
