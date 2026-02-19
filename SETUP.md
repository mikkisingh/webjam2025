# MediCheck — Setup Guide

Full step-by-step guide to run MediCheck locally.

---

## Prerequisites

| Requirement | Version | Check |
|-------------|---------|-------|
| Python | 3.8+ | `python3 --version` |
| Node.js | 16+ | `node --version` |
| npm | 7+ | `npm --version` |
| Tesseract OCR | 5.x | `tesseract --version` |
| Google Gemini API key | — | [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) |
| Supabase project | Free tier | [supabase.com](https://supabase.com) |

### Install Tesseract OCR

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt install tesseract-ocr
```

**Windows:**
Download from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki) and add to PATH.

---

## Step 1 — Supabase Database Setup

Run this **once** in your Supabase project to create the tables and Row Level Security policies.

1. Open [supabase.com](https://supabase.com) → your project
2. Go to **SQL Editor → New query**
3. Paste the contents of [`supabase_schema.sql`](supabase_schema.sql) and click **Run**

This creates:
- `analyses` table — stores AI analysis results (never raw bill content)
- `disputes` table — for Phase 2 dispute outcome tracking
- RLS policies that ensure users can only access their own data

---

## Step 2 — Backend Setup

```bash
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
```

Edit `backend/.env`:

```env
# Required — Google Gemini API key
GEMINI_API_KEY=your_gemini_api_key_here

# Optional — upload folder (relative path, defaults to 'uploads')
UPLOAD_FOLDER=uploads
```

> **Important:** Use a relative path for `UPLOAD_FOLDER` (e.g. `uploads`), never an absolute path starting with `/`.

### Start the backend

```bash
cd backend
python run.py
```

Backend starts at: **http://localhost:5001**

> **Note:** Port 5000 is used by macOS AirPlay Receiver. MediCheck uses port 5001.

The `uploads/` folder is created automatically. Uploaded files are deleted immediately after text extraction — nothing is stored persistently on the backend.

---

## Step 3 — Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Frontend starts at: **http://localhost:5173**

The Supabase client is pre-configured in `src/lib/supabase.js`. No additional frontend environment variables are needed for local development.

---

## Running Both Together

Open two terminal windows:

**Terminal 1 — Backend:**
```bash
cd webjam2025/backend
python run.py
```

**Terminal 2 — Frontend:**
```bash
cd webjam2025/frontend
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## User Flow

1. **Upload a bill** — no account required, the file is deleted immediately after analysis
2. **View results** — issues, charges, savings estimate, dispute email
3. **Sign up free** — to save results to your history and track dispute outcomes
4. **History page** — view all past analyses, update dispute status per bill

---

## Troubleshooting

### "GEMINI_API_KEY not found"
`backend/.env` must exist and contain a valid key. The `.env` file is never committed to git.

### "Could not extract text from this file"
- **PDF**: The file may be image-only (scanned). These are processed via OCR — ensure Tesseract is installed.
- **Images**: Tesseract must be on your PATH. Run `tesseract --version` to verify.

### CORS errors in the browser
Make sure the backend is running on port 5001. The frontend fetch calls are hardcoded to `http://localhost:5001`.

### Supabase "row-level security" errors
Make sure you ran `supabase_schema.sql` in the Supabase SQL editor. RLS must be enabled with the correct policies before the app can write data.

### Port 5001 already in use
```bash
lsof -ti :5001 | xargs kill -9
```

### Database errors (SQLite)
The `app.db` file is only used for the legacy `items` table. If corrupted, delete it and restart the backend — it will be recreated automatically.

---

## Build for Production

**Frontend:**
```bash
cd frontend
npm run build
# Output: frontend/dist/
```

**Backend** — use a production WSGI server:
```bash
pip install gunicorn
cd backend
gunicorn -w 4 app:app
```

For production deployment, set `FLASK_ENV=production` and configure HTTPS. The Supabase connection is handled entirely by the frontend SDK, so no backend environment changes are needed for Supabase.
