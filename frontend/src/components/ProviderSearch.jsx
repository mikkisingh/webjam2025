import { useState, useRef } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001'

const US_STATES = [
  '', 'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA',
  'KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ',
  'NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT',
  'VA','WA','WV','WI','WY','DC',
]

const SPECIALTIES = [
  '',
  'Family Medicine',
  'Internal Medicine',
  'Pediatrics',
  'Obstetrics & Gynecology',
  'Cardiology',
  'Dermatology',
  'Emergency Medicine',
  'Gastroenterology',
  'General Surgery',
  'Neurology',
  'Ophthalmology',
  'Orthopedic Surgery',
  'Psychiatry & Neurology',
  'Radiology',
  'Urology',
  'Physical Therapy',
  'Dentist',
  'Nurse Practitioner',
  'Physician Assistant',
]

export default function ProviderSearch() {
  const [zip, setZip]             = useState('')
  const [city, setCity]           = useState('')
  const [state, setState]         = useState('')
  const [specialty, setSpecialty] = useState('')
  const [results, setResults]     = useState(null)
  const [loading, setLoading]     = useState(false)
  const [error, setError]         = useState(null)
  const formRef                   = useRef(null)

  const doSearch = async (e) => {
    e.preventDefault()
    if (!zip && !city && !state) {
      setError('Enter at least a ZIP code, city, or state.')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const params = new URLSearchParams({ limit: 20 })
      if (zip)       params.set('zip', zip)
      if (city)      params.set('city', city)
      if (state)     params.set('state', state)
      if (specialty) params.set('specialty', specialty)

      const res = await fetch(`${API_URL}/providers/search?${params}`)
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.error || `Server error ${res.status}`)
      }
      const data = await res.json()
      setResults(data)
    } catch (err) {
      setError(err.message)
      setResults(null)
    } finally {
      setLoading(false)
    }
  }

  const formatPhone = (p) => {
    if (!p) return ''
    const d = p.replace(/\D/g, '')
    if (d.length === 10) return `(${d.slice(0,3)}) ${d.slice(3,6)}-${d.slice(6)}`
    return p
  }

  const formatZip = (z) => (z && z.length > 5 ? z.slice(0,5) : z)

  return (
    <div className="provider-search">
      <form className="ps-form" onSubmit={doSearch} ref={formRef}>
        <div className="ps-fields">
          <div className="ps-field">
            <label className="ps-label" htmlFor="ps-zip">ZIP Code</label>
            <input
              id="ps-zip"
              type="text"
              className="ps-input"
              placeholder="e.g. 90210"
              value={zip}
              onChange={(e) => setZip(e.target.value.replace(/\D/g, '').slice(0, 5))}
              inputMode="numeric"
              maxLength={5}
            />
          </div>

          <div className="ps-field">
            <label className="ps-label" htmlFor="ps-city">City</label>
            <input
              id="ps-city"
              type="text"
              className="ps-input"
              placeholder="e.g. Los Angeles"
              value={city}
              onChange={(e) => setCity(e.target.value)}
            />
          </div>

          <div className="ps-field">
            <label className="ps-label" htmlFor="ps-state">State</label>
            <select
              id="ps-state"
              className="ps-input ps-select"
              value={state}
              onChange={(e) => setState(e.target.value)}
            >
              <option value="">Any state</option>
              {US_STATES.filter(Boolean).map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>

          <div className="ps-field">
            <label className="ps-label" htmlFor="ps-specialty">Specialty</label>
            <select
              id="ps-specialty"
              className="ps-input ps-select"
              value={specialty}
              onChange={(e) => setSpecialty(e.target.value)}
            >
              <option value="">Any specialty</option>
              {SPECIALTIES.filter(Boolean).map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
        </div>

        <button className="button primary ps-submit" type="submit" disabled={loading}>
          {loading ? 'Searching…' : 'Find Providers'}
        </button>
      </form>

      {error && <p className="ps-error">{error}</p>}

      {results && (
        <>
          <p className="ps-count muted">
            {results.count === 0
              ? 'No providers found. Try broadening your search.'
              : `Showing ${results.count} of ${results.total.toLocaleString()} providers`}
          </p>

          {results.providers.length > 0 && (
            <div className="ps-grid">
              {results.providers.map((p) => (
                <article key={p.npi} className="ps-card">
                  <div className="ps-card-header">
                    <h4 className="ps-card-name">{p.name}</h4>
                    {p.specialty && (
                      <span className="ps-specialty-tag">{p.specialty}</span>
                    )}
                  </div>

                  <div className="ps-card-body">
                    {(p.address.line1 || p.address.city) && (
                      <div className="ps-card-row">
                        <span className="ps-card-icon">&#x1f4cd;</span>
                        <span>
                          {p.address.line1}
                          {p.address.line2 ? `, ${p.address.line2}` : ''}
                          <br />
                          {p.address.city}{p.address.state ? `, ${p.address.state}` : ''}{' '}
                          {formatZip(p.address.zip)}
                        </span>
                      </div>
                    )}

                    {p.phone && (
                      <div className="ps-card-row">
                        <span className="ps-card-icon">&#x1f4de;</span>
                        <a href={`tel:${p.phone}`} className="ps-phone">
                          {formatPhone(p.phone)}
                        </a>
                      </div>
                    )}
                  </div>

                  <div className="ps-card-footer">
                    <span className="ps-npi muted">NPI: {p.npi}</span>
                  </div>
                </article>
              ))}
            </div>
          )}
        </>
      )}

      <p className="ps-disclaimer">
        Provider data from the CMS National Plan &amp; Provider Enumeration System (NPPES).
        Listing does not imply endorsement. Verify coverage with your insurance.
      </p>
    </div>
  )
}
