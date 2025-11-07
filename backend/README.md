# MediCheck Backend API

Flask-based REST API for medical bill analysis using AI.

## Features

- **File Upload**: Accept PDF, JPG, PNG medical bills
- **Text Extraction**: Extract text using pdfplumber (PDF) and Tesseract (images)
- **AI Analysis**: Use Google Gemini 2.0 Flash for:
  - Data structuring (patient info, charges, dates)
  - Cost analysis (detect overcharges, duplicates)
  - Summary generation (human-readable + complaint emails)
- **Database Storage**: SQLite for bill tracking and history

## Setup

```bash
cd backend
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Create uploads directory
mkdir uploads
```

## Run

```bash
python run.py
```

Server will run on `http://127.0.0.1:5000`

## Endpoints

### Bill Analysis Endpoints
- `POST /upload` - Upload medical bill (PDF, JPG, PNG)
- `POST /analyze/<bill_id>` - Analyze uploaded bill with AI
- `GET /bills` - Get all bills
- `GET /bills/<bill_id>` - Get specific bill details

### Legacy Endpoints
- `GET /` - Health check
- `GET /items` - Get all items
- `POST /items` - Create new item

## Environment Variables

```env
GEMINI_API_KEY=your_api_key_here
UPLOAD_FOLDER=uploads
```

## Dependencies

- Flask, Flask-CORS, SQLAlchemy
- pdfplumber, pytesseract, Pillow
- google-generativeai, python-dotenv

**Note**: Tesseract OCR must be installed separately on your system.

