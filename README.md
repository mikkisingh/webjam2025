# MediCheck - Medical Bill Analysis Platform

An AI-powered web application that analyzes medical bills to detect overcharges, duplicate fees, and billing errors.

## Features

- **Smart Upload**: Drag-and-drop support for PDF, JPG, and PNG medical bills
- **AI Analysis**: Uses Google Gemini 2.0 Flash to:
  - Extract and structure bill data (patient info, charges, dates)
  - Detect overpriced services and duplicate charges
  - Identify missing insurance adjustments
  - Flag unbundled procedures
- **Detailed Results**: Color-coded issues, cost breakdowns, and potential savings
- **Dispute Templates**: Auto-generated professional email templates for billing departments
- **History Tracking**: Store and review past bill analyses

## Tech Stack

- **Backend**: Flask + SQLAlchemy + SQLite
- **Frontend**: React (Vite) + Modern CSS
- **AI**: Google Gemini 2.0 Flash
- **Text Extraction**: pdfplumber (PDF) + Tesseract OCR (images)

---

## Quick Start

See [SETUP.md](SETUP.md) for detailed installation instructions.

### Prerequisites
- Python 3.8+
- Node.js 16+
- Tesseract OCR
- Google Gemini API key

### Backend Setup

```powershell
cd backend
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Test setup
python test_setup.py

# Run server
python run.py
```

Backend runs on: `http://127.0.0.1:5000`

### Frontend Setup

```powershell
cd frontend
npm install
npm run dev
```

Frontend runs on: `http://127.0.0.1:5173`

---

## Project Structure

```
webjam2025/
├── backend/
│   ├── app.py              # Flask API endpoints
│   ├── models.py           # Database models (Bill, Item)
│   ├── database.py         # SQLAlchemy configuration
│   ├── text_extractor.py   # PDF/image text extraction
│   ├── llm_service.py      # OpenAI integration
│   ├── test_setup.py       # Setup verification script
│   ├── requirements.txt    # Python dependencies
│   ├── .env.example        # Environment template
│   └── uploads/            # Temporary file storage
│
└── frontend/
    ├── src/
    │   ├── App.jsx                  # Main application
    │   ├── components/
    │   │   ├── BillUpload.jsx      # File upload component
    │   │   └── BillAnalysis.jsx    # Results display
    │   └── index.css                # Styles
    ├── vite.config.js

    └── tailwind.config.js
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET    | `/`      | Health check |
| GET    | `/items` | Get all items |
| POST   | `/items` | Create item |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, Tailwind CSS |
| Backend | Flask, SQLAlchemy |
| Database | SQLite |

---

## Notes

- CORS is enabled for `http://127.0.0.1:5173`
- Database file (`app.db`) is auto-created in the backend folder
- Tailwind CSS errors in the editor are normal and will work when running

---


