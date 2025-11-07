import React, { useState, useEffect } from "react";
import Login from "./loginreg/loginpage.jsx";
import Register from "./loginreg/register.jsx";
import { auth } from "./loginreg/firebase.jsx";
import { onAuthStateChanged, signOut } from "firebase/auth";
import "./loginreg/styles.css";

function App() {
  var [page, setPage] = useState("login");
  var [user, setUser] = useState(null);
  var [year, setYear] = useState(new Date().getFullYear());
  var [toastMessage, setToastMessage] = useState("");

  function goToLogin() { setPage("login"); }
  function goToRegister() { setPage("register"); }
  function goToLanding() { setPage("landing"); }

  async function handleLogout() {
    await signOut(auth);
    setUser(null);
    setPage("login");
  }

  function toast(msg) {
    setToastMessage(msg);
    setTimeout(function() { setToastMessage(""); }, 2400);
  }

  function handleComingSoon() { toast("Coming soon — connect backend."); }

  useEffect(function() {
    var unsubscribe = onAuthStateChanged(auth, function(currentUser) {
      setUser(currentUser);
      if (currentUser) setPage("landing");
    });
    return function() { unsubscribe(); }
  }, []);

  if (page === "login") {
    return <Login onRegister={goToRegister} onSuccess={goToLanding} />;
  }

  if (page === "register") {
    return <Register onLogin={goToLogin} />;
  }

  return (
    <div>
      <header className="site-header">
        <div className="container header-inner">
          <div className="brand">
            <div className="logo" aria-hidden="true">✓</div>
            <h1 className="title">MediCheck</h1>
          </div>

          <nav className="nav" aria-label="Primary">
            <button className="button ghost" onClick={handleLogout}>
              Logout
            </button>
          </nav>
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
              <button className="button primary" onClick={handleComingSoon}>
                Check documents
              </button>
              <button className="button ghost" onClick={handleComingSoon}>
                Examine prices
              </button>
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
                <form className="inline-form" onSubmit={function(e){ e.preventDefault(); handleComingSoon(); }}>
                  <input type="file" aria-label="Choose document to check" />
                  <button className="button primary" type="submit">Check now</button>
                </form>
                <p className="coming-soon">Backend hookup pending — connect endpoint later.</p>
              </article>

              <article className="card">
                <div className="card-icon" aria-hidden="true">🔎</div>
                <h4>Document status</h4>
                <p>Look up the review status by reference ID.</p>
                <form className="inline-form" onSubmit={function(e){ e.preventDefault(); handleComingSoon(); }}>
                  <input type="text" placeholder="Enter reference ID" aria-label="Reference ID" />
                  <button className="button" type="submit">Check status</button>
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
                <form className="inline-form" onSubmit={function(e){ e.preventDefault(); handleComingSoon(); }}>
                  <input type="text" placeholder="e.g., MRI, CPT 70551" aria-label="Procedure" />
                  <button className="button primary" type="submit">Search</button>
                </form>
                <p className="coming-soon">Results table will render here.</p>
              </article>

              <article className="card">
                <div className="card-icon" aria-hidden="true">🧭</div>
                <h4>Nearby providers</h4>
                <p>Explore providers by distance and price transparency.</p>
                <form className="inline-form" onSubmit={function(e){ e.preventDefault(); handleComingSoon(); }}>
                  <input type="text" placeholder="ZIP or City" aria-label="Location" />
                  <button className="button" type="submit">Explore</button>
                </form>
                <p className="coming-soon">Hook to geosearch + pricing API.</p>
              </article>
            </div>
          </div>
        </section>
      </main>

      <footer className="site-footer">
        <div className="container footer-inner">
          <p className="muted">© {year} MediCheck. All rights reserved.</p>
        </div>
      </footer>

      {/* Toast */}
      {toastMessage && <div className="toast show">{toastMessage}</div>}
    </div>
  );
}

export default App;
