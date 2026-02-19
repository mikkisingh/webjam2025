# MediCheck — Architecture Overview

## System Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                           Browser                              │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                React Frontend (Vite)                     │  │
│  │                http://localhost:5173                     │  │
│  │                                                          │  │
│  │  App.jsx (view routing + auth state)                     │  │
│  │  ├── AuthModal.jsx      (sign in / sign up modal)        │  │
│  │  ├── BillUpload.jsx     (drag-drop + file picker)        │  │
│  │  ├── BillAnalysis.jsx   (results display + save)         │  │
│  │  └── BillHistory.jsx    (saved analyses + disputes)      │  │
│  │                                                          │  │
│  │  context/AuthContext.jsx  (useAuth hook, auth state)     │  │
│  │  lib/supabase.js          (Supabase client instance)     │  │
│  └──────────┬──────────────────────────┬─────────────────────┘  │
└─────────────┼──────────────────────────┼──────────────────────┘
              │ multipart/form-data       │ Supabase JS SDK
              │ POST /process             │ (direct from browser)
              ▼                           ▼
┌───────────────────────────┐  ┌──────────────────────────────┐
│   Flask Backend (Python)  │  │   Supabase (PostgreSQL)      │
│   http://localhost:5001   │  │   Auth + Database            │
│                           │  │                              │
│   app.py                  │  │   analyses table (RLS)       │
│   ├── POST /process       │  │   disputes table (Phase 2)   │
│   ├── GET  /              │  │                              │
│   └── GET|POST /items     │  │   Row Level Security:        │
│         (legacy)          │  │   user_id = auth.uid()       │
│                           │  └──────────────────────────────┘
│   text_extractor.py       │
│   llm_service.py          │ HTTPS
│                           │────────────────────►
└───────────────────────────┘          ┌──────────────────┐
                                       │  Google Gemini   │
                                       │  2.0 Flash API   │
                                       └──────────────────┘
```

**Key design principle:** The Flask backend is a **stateless compute layer** only.
It processes the uploaded file and returns results in a single call — it never stores
bill content or analysis results. All persistence is handled by the frontend writing
directly to Supabase via the JS SDK.

---

## Directory Structure

```
webjam2025/
├── README.md               # Project overview
├── SETUP.md                # Installation and setup guide
├── API.md                  # API reference documentation
├── ARCHITECTURE.md         # This file
├── PRD.md                  # Product requirements document
├── supabase_schema.sql     # Run once in Supabase SQL Editor
│
├── backend/
│   ├── app.py              # Flask API — single /process endpoint
│   ├── run.py              # Dev server entry point (port 5001)
│   ├── database.py         # SQLAlchemy config (legacy items table only)
│   ├── models.py           # ORM model: Item (legacy)
│   ├── llm_service.py      # Google Gemini integration (LLMAnalyzer)
│   ├── text_extractor.py   # PDF/image text extraction (TextExtractor)
│   ├── requirements.txt    # Python dependencies
│   ├── .env                # Local environment variables (gitignored)
│   ├── .env.example        # Environment variable template
│   ├── app.db              # SQLite (legacy items table only, gitignored)
│   └── uploads/            # Temp folder — files deleted after extraction
│
└── frontend/
    ├── index.html
    ├── vite.config.js
    ├── package.json
    └── src/
        ├── main.jsx                    # React entry point (AuthProvider wrapper)
        ├── App.jsx                     # Root layout + view state machine
        ├── index.css                   # Global styles
        ├── lib/
        │   └── supabase.js             # Supabase client (URL + anon key)
        ├── context/
        │   └── AuthContext.jsx         # Auth state + useAuth hook
        └── components/
            ├── AuthModal.jsx           # Sign in / Sign up modal
            ├── BillUpload.jsx          # File upload + POST /process
            ├── BillAnalysis.jsx        # Results display + Supabase save
            └── BillHistory.jsx         # History list + dispute tracker
```

---

## Data Flow: Bill Analysis Pipeline

```
User selects/drops file
        │
        ▼
BillUpload.jsx: POST /process  (multipart/form-data)
        │
        ▼
Flask app.py — /process endpoint
        │
        ├─ Validate file type (PDF, JPG, PNG) and size (≤ 16MB)
        ├─ Save to uploads/ with uuid prefix
        ├─ TextExtractor.extract_text()
        │     ├─ PDF  → pdfplumber (text layer extraction)
        │     └─ Image → pytesseract (Tesseract OCR)
        ├─ DELETE file from disk immediately  ← HIPAA Option A
        ├─ LLMAnalyzer.analyze_bill(raw_text)
        │     ├─ 1. extract_structured_data()   [Gemini call 1]
        │     │      → JSON: patient, provider, charges, total
        │     ├─ 2. analyze_costs()              [Gemini call 2]
        │     │      → JSON: issues, severity, potential_savings
        │     └─ 3. generate_summary()           [Gemini call 3]
        │            → summary text + dispute email template
        └─ Return all results in single response (nothing stored)
                │
                ▼
        BillAnalysis.jsx receives full data object
                │
                ├─ Renders results immediately (no account required)
                │
                └─ If user is authenticated:
                        └─ supabase.from('analyses').insert(...)
                           (AI output only — no raw bill text)
```

---

## Supabase Schema

### `analyses` table

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID PK | `uuid_generate_v4()` |
| `user_id` | UUID FK | References `auth.users(id)` — RLS key |
| `created_at` | TIMESTAMPTZ | Auto-set on insert |
| `bill_nickname` | TEXT | Optional user-provided label |
| `file_type` | TEXT | `pdf`, `jpg`, `png` |
| `overall_severity` | TEXT | `low` / `medium` / `high` |
| `potential_savings` | NUMERIC | Estimated recoverable amount |
| `issues_count` | INTEGER | Number of billing issues found |
| `structured_data` | JSONB | Patient info, charges, totals |
| `analysis_results` | JSONB | Issues, severity, recommendations |
| `summary` | TEXT | Human-readable Gemini summary |
| `complaint_email` | TEXT | Auto-generated dispute email |
| `dispute_status` | TEXT | `none` / `submitted` / `in_progress` / `resolved` / `rejected` |

**Row Level Security policies:**
- `SELECT` — `auth.uid() = user_id`
- `INSERT` — `auth.uid() = user_id`
- `UPDATE` — `auth.uid() = user_id`
- `DELETE` — `auth.uid() = user_id`

### `disputes` table (Phase 2 — created, not yet used)

Tracks dispute outcomes with provider contact details, response dates, and resolution amounts.

### `items` table (legacy — SQLite only)

Still created in `app.db` for the `/items` legacy endpoints. Bill data is never stored here.

---

## Key Technology Choices

| Component | Technology | Reason |
|-----------|------------|--------|
| Backend framework | Flask | Lightweight stateless compute layer |
| PDF extraction | pdfplumber | Reliable text-layer PDF parsing |
| Image OCR | Tesseract (pytesseract) | Industry-standard open-source OCR |
| AI analysis | Google Gemini 2.0 Flash | Fast, JSON-mode responses, cost-effective |
| Frontend | React 18 + Vite | Fast HMR, modern React patterns |
| Auth | Supabase Auth | Email/password + Google OAuth, zero backend config |
| Database | Supabase (PostgreSQL) | Managed DB + RLS, free tier, JS SDK |
| Legacy ORM | SQLAlchemy + SQLite | Retained for `/items` legacy endpoints only |

---

## Frontend Component Responsibilities

### `AuthContext.jsx`
- Wraps the entire app via `<AuthProvider>`
- Exposes `user`, `loading`, `signIn`, `signUp`, `signInWithGoogle`, `signOut` via `useAuth` hook
- Subscribes to `supabase.auth.onAuthStateChange` to keep state in sync across tabs

### `App.jsx`
- Top-level layout: header, hero, main section, footer
- **View state machine**: `'main'` → `'history'` → `'history-detail'`
- Shows authenticated user menu (avatar, History nav, Sign out)
- Shows guest header (Sign in / Sign up free)
- Passes `onRequestAuth` down to `BillAnalysis` to trigger `AuthModal`

### `AuthModal.jsx`
- Tabbed modal: Sign In / Sign Up
- Email + password form for both modes
- Google OAuth button (`signInWithGoogle`)
- Shows success message for sign-up (email confirmation flow)
- Receives `initialMode` prop and `onClose` callback

### `BillUpload.jsx`
- Drag-and-drop file zone + `<input type="file">` fallback
- Client-side validation (type + size ≤ 16MB)
- POSTs to `http://localhost:5001/process` as `multipart/form-data`
- Calls `onUploadSuccess(data)` with the full analysis result object

### `BillAnalysis.jsx`
- Pure display component — receives `billData` prop, makes no API calls
- `fromHistory` prop: if `true`, skips the Supabase save attempt
- Auto-saves to Supabase via `useEffect` when `user` becomes available
- Shows: `Saving...` chip → `Saved to history` chip, or `Sign up free` save prompt
- Renders: summary, bill details, charges table, issues list, recommendations, dispute email
- Copy-to-clipboard for dispute email

### `BillHistory.jsx`
- Fetches all user analyses from Supabase on mount (ordered newest first)
- Summary bar: total bills, total potential savings, confirmed savings (resolved disputes)
- Per-row: severity icon, provider, patient, date, issues count, savings, bill total
- Inline `<select>` for dispute status — updates Supabase on change
- Delete button with `confirm()` dialog

---

## Auth Flow

```
User clicks "Sign up free"
        │
        ▼
AuthModal opens (signup tab)
        │
        ├─ Email + password → supabase.auth.signUp()
        │   → Supabase sends confirmation email
        │   → onAuthStateChange fires when confirmed
        │
        └─ Google OAuth → supabase.auth.signInWithOAuth({ provider: 'google' })
            → Redirect to Google consent
            → Redirect back → onAuthStateChange fires
                │
                ▼
        AuthContext: setUser(session.user)
                │
                ▼
        BillAnalysis: useEffect([user]) triggers → saveToSupabase()
```

---

## Known Limitations & Future Work

- **No pagination** — `GET /bills` (legacy) and Supabase history fetch return all rows; add limit/offset for large datasets
- **Single-language OCR** — Tesseract configured for English only; multilingual support requires additional language packs
- **No retry logic** — if a Gemini call fails mid-pipeline, the entire `/process` request fails with a 500; partial results are lost
- **Google OAuth requires Supabase dashboard config** — the "Continue with Google" button is implemented but requires enabling the Google provider in the Supabase Auth settings
- **Hardcoded backend URL** — `http://localhost:5001` is hardcoded in `BillUpload.jsx`; move to an env variable (`VITE_API_URL`) for production deployment
- **`disputes` table unused** — created in schema for Phase 2 dispute outcome tracking with provider contact details; not yet surfaced in the UI
