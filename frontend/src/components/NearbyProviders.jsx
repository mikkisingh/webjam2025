import { useState } from "react";

// Point to your Flask backend; override via Vite env if you like
const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:5000";

export default function NearbyProviders() {
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [results, setResults] = useState([]);

  async function search() {
    if (!q.trim()) { setStatus("Enter a city or ZIP"); return; }
    try {
      setStatus("Searching nearby providers…");
      const res = await fetch(`${API_BASE}/api/nearby?q=${encodeURIComponent(q)}&limit=25`);
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || `HTTP ${res.status}`);
      }
      const data = await res.json();
      setResults(data.results || []);
      setStatus(`Showing closest ${data.count}.`);
    } catch (e) {
      console.error(e);
      setStatus("Something went wrong. See console.");
      setResults([]);
    }
  }

  return (
    <article className="card">
      <div className="card-icon" aria-hidden="true">🧭</div>
      <h4>Nearby providers</h4>
      <p>Explore providers by distance and price transparency.</p>

      <form
        className="inline-form"
        onSubmit={(e) => { e.preventDefault(); search(); }}
      >
        <input
          type="text"
          placeholder="ZIP or City"
          aria-label="Location"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <button className="button" type="submit">Search</button>
      </form>

      <div className="status-row">{status}</div>

      <div className="nearby-grid">
        {results.map((r, i) => {
          const maps = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(r.name)}`;
          return (
            <div className="nearby-card" key={i}>
              <div className="nearby-card__icon" aria-hidden="true">🏥</div>
              <div className="nearby-card__content">
                <div className="nearby-card__title">{r.name}</div>
                <div className="nearby-card__meta">
                  <span>{r.distance.toFixed(1)} mi</span>
                  {r.formatted ? <span> · {r.formatted}</span> : null}
                </div>
              </div>
              <a className="button small" href={maps} target="_blank" rel="noopener">Map</a>
            </div>
          );
        })}
      </div>
    </article>
  );
}
