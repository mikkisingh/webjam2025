import { useState, useEffect } from "react";

function App() {
  const [year, setYear] = useState(new Date().getFullYear());

  const toast = (msg) => {
    const t = document.createElement('div');
    t.className = 'toast';
    t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(() => t.classList.add('show'), 10);
    setTimeout(() => { 
      t.classList.remove('show'); 
      setTimeout(() => t.remove(), 200);
    }, 2400);
  };

  const handleClick = (e) => {
    e.preventDefault();
    toast('Coming soon — connect backend.');
  };

  return (
    <>
      <header className="site-header">
        <div className="container header-inner">
          <div className="brand">
            <div className="logo" aria-hidden="true">✓</div>
            <h1 className="title">MediCheck</h1>
          </div>
          <nav className="nav" aria-label="Primary"></nav>
        </div>
      </header>

      <main>
        <section className="hero">
          <div className="container hero-inner">
            <h2 className="hero-title">Verify documents. Compare prices.</h2>
            <p className="hero-subtitle">
              A simple, trustworthy place to check healthcare documents and explore fair pricing.
            </p>
            <div className="hero-cta">
              <a href="#documents" className="button primary">Check documents</a>
              <a href="#prices" className="button ghost">Examine prices</a>
            </div>
          </div>
        </section>

        <section id="documents" className="section">
          <div className="container">
            <div className="section-head">
              <h3>Document Check</h3>
              <p>Upload and validate files for authenticity and completeness.</p>
            </div>

            <div className="card-grid">
              <article className="card">
                <div className="card-icon" aria-hidden="true">📄</div>
                <h4>Upload a document</h4>
                <p>We'll scan and flag issues (missing fields, mismatched IDs, etc.).</p>

                <form className="inline-form" onSubmit={(e) => e.preventDefault()}>
                  <input type="file" aria-label="Choose document to check" />
                  <button className="button primary" type="button" onClick={handleClick}>
                    Check now
                  </button>
                </form>

                <p className="coming-soon">Backend hookup pending — connect endpoint later.</p>
              </article>

              <article className="card">
                <div className="card-icon" aria-hidden="true">🔎</div>
                <h4>Document status</h4>
                <p>Look up the review status by reference ID.</p>

                <form className="inline-form" onSubmit={(e) => e.preventDefault()}>
                  <input type="text" placeholder="Enter reference ID" aria-label="Reference ID" />
                  <button className="button" type="button" onClick={handleClick}>
                    Check status
                  </button>
                </form>

                <p className="coming-soon">Stub UI only — add fetch to your API.</p>
              </article>
            </div>
          </div>
        </section>

        <section id="prices" className="section alt">
          <div className="container">
            <div className="section-head">
              <h3>Price Explorer</h3>
              <p>Compare procedure costs across providers and insurance networks.</p>
            </div>

            <div className="card-grid">
              <article className="card">
                <div className="card-icon" aria-hidden="true">🏥</div>
                <h4>Search by procedure</h4>
                <p>Find typical cash prices and negotiated rates (where available).</p>

                <form className="inline-form" onSubmit={(e) => e.preventDefault()}>
                  <input type="text" placeholder="e.g., MRI, CPT 70551" aria-label="Procedure" />
                  <button className="button primary" type="button" onClick={handleClick}>
                    Search
                  </button>
                </form>

                <p className="coming-soon">Results table will render here.</p>
              </article>

              <article className="card">
                <div className="card-icon" aria-hidden="true">🧭</div>
                <h4>Nearby providers</h4>
                <p>Explore providers by distance and price transparency.</p>

                <form className="inline-form" onSubmit={(e) => e.preventDefault()}>
                  <input type="text" placeholder="ZIP or City" aria-label="Location" />
                  <button className="button" type="button" onClick={handleClick}>
                    Explore
                  </button>
                </form>

                <p className="coming-soon">Hook to geosearch + pricing API.</p>
              </article>
            </div>
          </div>
        </section>
      </main>

      <footer className="site-footer">
        <div className="container footer-inner">
          <p className="muted">© <span id="year">{year}</span> MediCheck. All rights reserved.</p>
        </div>
      </footer>
    </>
  );
}

export default App;
