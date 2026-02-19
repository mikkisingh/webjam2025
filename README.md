# MediCheck — AI-Powered Medical Bill Analysis

An AI-powered web application that helps patients detect overcharges, duplicate fees, and billing errors in their medical bills — and generate dispute emails to fight back.

> **Privacy-first:** Your uploaded file is deleted from our server the moment text is extracted. Raw bill content is never persisted. Analysis results are stored securely in Supabase, scoped to your account only.

---

## Features

- **Smart Upload** — Drag-and-drop or browse for PDF, JPG, and PNG medical bills
- **AI Analysis** — Google Gemini 2.0 Flash extracts charges, detects overprices/duplicates, flags unbundled procedures
- **Detailed Results** — Color-coded issues, charges breakdown, potential savings estimate
- **Dispute Email Generator** — Auto-generated professional email template ready to send to billing departments
- **Bill History** — Save and review past analyses (requires free account)
- **Dispute Tracker** — Track the status of each dispute (submitted / in progress / resolved / rejected)
- **User Accounts** — Email/password or Google sign-in via Supabase Auth

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite |
| Auth & Database | Supabase (PostgreSQL + Row Level Security) |
| Backend | Flask (Python) — stateless compute only |
| AI | Google Gemini 2.0 Flash |
| PDF extraction | pdfplumber |
| Image OCR | Tesseract (pytesseract) |

---

## Quick Start

See [SETUP.md](SETUP.md) for the full step-by-step guide.

### Prerequisites

- Python 3.8+
- Node.js 16+
- Tesseract OCR (`brew install tesseract` on macOS)
- Google Gemini API key — [get one here](https://aistudio.google.com/app/apikey)
- Supabase project (free tier) — [supabase.com](https://supabase.com)

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Add your GEMINI_API_KEY to .env
python run.py
```

Backend runs on: `http://localhost:5001`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on: `http://localhost:5173`

---

## Project Structure

```
webjam2025/
├── README.md               # This file
├── SETUP.md                # Full installation guide
├── API.md                  # API reference
├── ARCHITECTURE.md         # System design and data flow
├── PRD.md                  # Product requirements document
├── supabase_schema.sql     # Run once in Supabase SQL Editor
│
├── backend/
│   ├── app.py              # Flask API (single /process endpoint)
│   ├── run.py              # Dev server entry point
│   ├── database.py         # SQLAlchemy config (legacy items only)
│   ├── models.py           # ORM models
│   ├── llm_service.py      # Google Gemini integration
│   ├── text_extractor.py   # PDF/image text extraction
│   ├── requirements.txt    # Python dependencies
│   ├── .env.example        # Environment variable template
│   └── uploads/            # Temp folder (files deleted after extraction)
│
└── frontend/
    ├── index.html
    ├── vite.config.js
    ├── package.json
    └── src/
        ├── main.jsx                    # React entry point (AuthProvider)
        ├── App.jsx                     # Root layout + view routing
        ├── index.css                   # Global styles
        ├── lib/
        │   └── supabase.js             # Supabase client
        ├── context/
        │   └── AuthContext.jsx         # Auth state (useAuth hook)
        └── components/
            ├── AuthModal.jsx           # Sign in / Sign up modal
            ├── BillUpload.jsx          # File upload + /process call
            ├── BillAnalysis.jsx        # Results display + Supabase save
            └── BillHistory.jsx         # Saved analyses + dispute tracker
```

---

## API

| Method | Endpoint    | Description |
|--------|-------------|-------------|
| GET    | `/`         | Health check |
| POST   | `/process`  | Upload bill → extract → analyze → delete file → return results |
| GET    | `/items`    | Legacy items list |
| POST   | `/items`    | Legacy item creation |

See [API.md](API.md) for full request/response documentation.

---

## Notes

- CORS is enabled globally on the backend
- The `uploads/` folder is auto-created but files are deleted immediately after text extraction
- SQLite (`app.db`) is still created for the legacy `items` table — bill data is never stored there
- Supabase RLS policies ensure users can only ever read their own analyses
