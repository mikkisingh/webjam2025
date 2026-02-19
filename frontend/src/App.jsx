import { useState, useEffect } from 'react'
import { useAuth } from './context/AuthContext'
import { useCredits } from './context/CreditsContext'
import { supabase } from './lib/supabase'
import BillUpload from './components/BillUpload'
import BillAnalysis from './components/BillAnalysis'
import BillHistory from './components/BillHistory'
import AdminDashboard from './components/AdminDashboard'
import AuthModal from './components/AuthModal'
import PriceExplorer from './components/PriceExplorer'
import ProviderSearch from './components/ProviderSearch'
import PurchaseModal from './components/PurchaseModal'

function App() {
  const { user, signOut, loading, isAdmin } = useAuth()
  const { credits, freeScanUsed, refreshCredits } = useCredits()
  const [currentAnalysis, setCurrentAnalysis] = useState(null)
  const [view, setView] = useState('main')
  const [historyAnalysis, setHistoryAnalysis] = useState(null)
  const [authModalOpen, setAuthModalOpen] = useState(false)
  const [authModalMode, setAuthModalMode] = useState('signin')
  const [purchaseModalOpen, setPurchaseModalOpen] = useState(false)
  const [publicStats, setPublicStats] = useState(null)
  const year = new Date().getFullYear()

  useEffect(() => {
    supabase.rpc('get_public_stats').then(({ data }) => {
      if (data) setPublicStats(data)
    })

    // Handle Stripe payment redirect
    const params = new URLSearchParams(window.location.search)
    if (params.get('payment') === 'success') {
      toast('Payment successful! Credits added to your account.')
      refreshCredits()
      window.history.replaceState({}, '', window.location.pathname)
    } else if (params.get('payment') === 'cancelled') {
      toast('Payment cancelled.')
      window.history.replaceState({}, '', window.location.pathname)
    }
  }, [])

  const navigateTo = (newView) => {
    setView(newView)
    window.scrollTo({ top: 0, behavior: 'instant' })
  }

  const toast = (msg) => {
    const t = document.createElement('div')
    t.className = 'toast'
    t.textContent = msg
    document.body.appendChild(t)
    setTimeout(() => t.classList.add('show'), 10)
    setTimeout(() => { t.classList.remove('show'); setTimeout(() => t.remove(), 200) }, 2400)
  }

  const handleUploadSuccess = (data) => {
    setCurrentAnalysis(data)
    toast('Bill analyzed successfully!')
  }

  const openAuthModal = (mode = 'signup') => {
    setAuthModalMode(mode)
    setAuthModalOpen(true)
  }

  const handleSignOut = async () => {
    await signOut()
    setCurrentAnalysis(null)
    navigateTo('main')
    toast('Signed out')
  }

  const handleViewHistoryItem = (analysis) => {
    setHistoryAnalysis(analysis)
    navigateTo('history-detail')
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
        <div className="loading-spinner" style={{ fontSize: 40 }}>⏳</div>
      </div>
    )
  }

  return (
    <>
      <header className="site-header">
        <div className="container header-inner">
          <div className="brand" style={{ cursor: 'pointer' }} onClick={() => navigateTo('main')}>
            <div className="logo" aria-hidden="true">✓</div>
            <h1 className="title">MediCheck</h1>
          </div>

          <nav className="nav" aria-label="Primary">
            {user ? (
              <div className="user-menu">
                {isAdmin && (
                  <button
                    className={`button ghost ${view === 'admin' ? 'nav-active' : ''}`}
                    onClick={() => navigateTo('admin')}
                  >
                    Admin
                  </button>
                )}
                <button
                  className={`button ghost ${view === 'history' || view === 'history-detail' ? 'nav-active' : ''}`}
                  onClick={() => navigateTo('history')}
                >
                  History
                </button>
                <button
                  className="credit-badge"
                  onClick={() => setPurchaseModalOpen(true)}
                  title="Scan credits — click to purchase"
                >
                  {credits === null ? '...' : !freeScanUsed ? '1 free' : `${credits} credit${credits !== 1 ? 's' : ''}`}
                </button>
                <div className="user-avatar" title={user.email}>
                  {user.email[0].toUpperCase()}
                </div>
                <button className="button ghost" onClick={handleSignOut}>Sign out</button>
              </div>
            ) : (
              <div className="user-menu">
                <button className="button ghost" onClick={() => openAuthModal('signin')}>Sign in</button>
                <button className="button primary" onClick={() => openAuthModal('signup')}>Sign up free</button>
              </div>
            )}
          </nav>
        </div>
      </header>

      <main>
        {/* ── Landing page ── */}
        {view === 'main' && (
          <div className="view-container">
            <section className="hero">
              <div className="container hero-inner">
                <h2 className="hero-title">Your medical bills, verified.</h2>
                <p className="hero-subtitle">
                  AI-powered bill analysis, Medicare price comparison across 100K+ procedure codes, and provider lookup — all in one place.
                </p>
              </div>
            </section>

            {publicStats && publicStats.total_analyses > 0 && (
              <div className="impact-bar">
                <div className="container">
                  <span className="impact-stat">
                    <span className="impact-stat-value">{Number(publicStats.total_analyses).toLocaleString()}</span>
                    {' '}bills analyzed
                  </span>
                  <span className="impact-stat-divider">·</span>
                  <span className="impact-stat">
                    <span className="impact-stat-value">${Number(publicStats.total_potential_savings).toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                    {' '}in potential savings identified
                  </span>
                </div>
              </div>
            )}

            <section className="section">
              <div className="container">
                <div className="feature-cards">
                  <button className="feature-card" onClick={() => navigateTo('scan')}>
                    <div className="feature-card-icon">📋</div>
                    <h3 className="feature-card-title">Scan Bill</h3>
                    <p className="feature-card-desc">
                      Upload your medical bill for AI-powered analysis. Detect overcharges, duplicate fees, and billing errors instantly.
                    </p>
                    <span className="feature-card-cta">Get started →</span>
                  </button>

                  <button className="feature-card" onClick={() => navigateTo('prices')}>
                    <div className="feature-card-icon">💲</div>
                    <h3 className="feature-card-title">Compare Prices</h3>
                    <p className="feature-card-desc">
                      Look up 100K+ procedure codes with Medicare rates, RVU breakdowns, HCPCS supplies, and ICD-10 codes.
                    </p>
                    <span className="feature-card-cta">Explore prices →</span>
                  </button>

                  <button className="feature-card" onClick={() => navigateTo('providers')}>
                    <div className="feature-card-icon">🏥</div>
                    <h3 className="feature-card-title">Find Providers</h3>
                    <p className="feature-card-desc">
                      Search the CMS national registry for healthcare providers by ZIP code, city, or specialty.
                    </p>
                    <span className="feature-card-cta">Search providers →</span>
                  </button>
                </div>
              </div>
            </section>
          </div>
        )}

        {/* ── Scan Bill view ── */}
        {view === 'scan' && (
          <div className="view-container">
            <div className="section">
              <div className="container">
                <button className="back-btn" onClick={() => navigateTo('main')}>
                  ← Back to Home
                </button>
                <div className="page-header">
                  <div className="page-header-icon">📋</div>
                  <div>
                    <h2>Scan Your Bill</h2>
                    <p className="muted">Upload a medical bill for instant AI-powered analysis. Your file is deleted the moment text is extracted.</p>
                  </div>
                </div>
                <BillUpload onUploadSuccess={handleUploadSuccess} />
                {currentAnalysis && (
                  <div style={{ marginTop: 32 }}>
                    <BillAnalysis
                      billData={currentAnalysis}
                      onRequestAuth={() => openAuthModal('signup')}
                    />
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ── Price Explorer view ── */}
        {view === 'prices' && (
          <div className="view-container">
            <div className="section">
              <div className="container">
                <button className="back-btn" onClick={() => navigateTo('main')}>
                  ← Back to Home
                </button>
                <div className="page-header">
                  <div className="page-header-icon">💲</div>
                  <div>
                    <h2>Price Explorer</h2>
                    <p className="muted">Look up procedure costs based on CMS Medicare rates and RVU data.</p>
                  </div>
                </div>
                <PriceExplorer />
              </div>
            </div>
          </div>
        )}

        {/* ── Provider Search view ── */}
        {view === 'providers' && (
          <div className="view-container">
            <div className="section">
              <div className="container">
                <button className="back-btn" onClick={() => navigateTo('main')}>
                  ← Back to Home
                </button>
                <div className="page-header">
                  <div className="page-header-icon">🏥</div>
                  <div>
                    <h2>Find Providers</h2>
                    <p className="muted">Search for healthcare providers by ZIP code, city, or specialty using the CMS national registry.</p>
                  </div>
                </div>
                <ProviderSearch />
              </div>
            </div>
          </div>
        )}

        {/* ── History detail view ── */}
        {view === 'history-detail' && historyAnalysis && (
          <div className="view-container">
            <div className="section">
              <div className="container">
                <button className="back-btn" onClick={() => navigateTo('history')}>
                  ← Back to History
                </button>
                <BillAnalysis
                  billData={historyAnalysis}
                  fromHistory={true}
                  onRequestAuth={() => openAuthModal('signup')}
                />
              </div>
            </div>
          </div>
        )}

        {/* ── History list view ── */}
        {view === 'history' && (
          <div className="view-container">
            <BillHistory
              onBack={() => navigateTo('main')}
              onViewAnalysis={handleViewHistoryItem}
            />
          </div>
        )}

        {/* ── Admin dashboard view ── */}
        {view === 'admin' && isAdmin && (
          <div className="view-container">
            <AdminDashboard onBack={() => navigateTo('main')} />
          </div>
        )}

        {/* ── Privacy Policy ── */}
        {view === 'privacy' && (
          <div className="view-container">
            <div className="section">
              <div className="container legal-page">
                <button className="back-btn" onClick={() => navigateTo('main')}>← Back to Home</button>
                <h2>Privacy Policy</h2>
                <p className="muted">Last updated: {new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}</p>

                <h3>What We Collect</h3>
                <p>When you create an account, we store your email address and authentication credentials via Supabase. If you choose to save an analysis, we store the analysis results (structured data, issues found, and summary) linked to your account.</p>

                <h3>Bill Processing</h3>
                <p>When you upload a bill for analysis, the file is processed in-memory and <strong>deleted immediately</strong> after text extraction. We do not retain, store, or log the original file or its raw text content on our servers.</p>

                <h3>Third-Party Services</h3>
                <p>Extracted text is sent to OpenAI for analysis. OpenAI's data usage policies apply to that processing. We also use Supabase for authentication and data storage, and CMS public APIs for price and provider data.</p>

                <h3>Data Retention</h3>
                <p>Saved analyses are retained until you delete them. You can delete any analysis from your History page at any time. Account deletion requests can be sent to the site administrator.</p>

                <h3>No Tracking</h3>
                <p>We do not use cookies for tracking, advertising pixels, or third-party analytics. We do not sell or share your data with third parties for marketing purposes.</p>
              </div>
            </div>
          </div>
        )}

        {/* ── Terms of Service ── */}
        {view === 'terms' && (
          <div className="view-container">
            <div className="section">
              <div className="container legal-page">
                <button className="back-btn" onClick={() => navigateTo('main')}>← Back to Home</button>
                <h2>Terms of Service</h2>
                <p className="muted">Last updated: {new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}</p>

                <h3>Service Description</h3>
                <p>MediCheck is an AI-powered tool that analyzes medical bills for potential billing errors, overcharges, and provides price comparisons using public Medicare data. The service is provided "as is" without warranty.</p>

                <h3>Not Professional Advice</h3>
                <p><strong>MediCheck does not provide medical, legal, or financial advice.</strong> Analysis results are AI-generated estimates based on public pricing data and should be used for informational purposes only. Always consult your healthcare provider, insurer, or a billing advocate for definitive guidance on your bills.</p>

                <h3>Accuracy</h3>
                <p>While we strive for accuracy, AI analysis may contain errors. Medicare pricing data is sourced from CMS public datasets and may not reflect your specific insurance plan, geographic area, or negotiated rates. You should verify all information independently.</p>

                <h3>User Responsibilities</h3>
                <p>You are responsible for the accuracy of files you upload. Do not upload documents containing information about other individuals without their consent. You agree not to use the service for any unlawful purpose or to abuse the API.</p>

                <h3>Limitation of Liability</h3>
                <p>MediCheck and its operators shall not be liable for any direct, indirect, incidental, or consequential damages arising from use of this service, including but not limited to financial decisions made based on analysis results.</p>
              </div>
            </div>
          </div>
        )}
      </main>

      <footer className="site-footer">
        <div className="container footer-inner">
          <p className="muted">© {year} MediCheck. Your bill is never stored on our servers.</p>
          <p className="muted footer-disclaimer">
            This tool provides informational estimates only and is not medical, legal, or financial advice. Always consult your provider or insurer for billing questions.
          </p>
          <div className="footer-links">
            <button className="footer-link" onClick={() => navigateTo('privacy')}>Privacy Policy</button>
            <span className="footer-sep">·</span>
            <button className="footer-link" onClick={() => navigateTo('terms')}>Terms of Service</button>
          </div>
        </div>
      </footer>

      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        initialMode={authModalMode}
      />
      <PurchaseModal
        isOpen={purchaseModalOpen}
        onClose={() => setPurchaseModalOpen(false)}
      />
    </>
  )
}

export default App
