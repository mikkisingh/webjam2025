# MediCheck - Medical Bill Analysis Setup Guide

## 🎯 Overview
MediCheck is a web application that analyzes medical bills using AI. It extracts text from PDFs and images, identifies overcharges, duplicate fees, and billing errors.

## 📋 Prerequisites

### Required Software
1. **Python 3.8+** - Backend runtime
2. **Node.js 16+** - Frontend runtime
3. **Tesseract OCR** - For image text extraction
   - **Windows**: Download from https://github.com/UB-Mannheim/tesseract/wiki
   - **Mac**: `brew install tesseract`
   - **Linux**: `sudo apt-get install tesseract-ocr`
4. **Google Gemini API Key** - For AI analysis (get from https://aistudio.google.com/app/apikey)

---

## 🔧 Backend Setup

### 1. Navigate to Backend Directory
```powershell
cd backend
```

### 2. Create Virtual Environment (Recommended)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the `backend` directory:

```env
# Google Gemini API Key for LLM analysis
GEMINI_API_KEY=your_gemini_api_key_here

# Upload folder for temporary file storage
UPLOAD_FOLDER=uploads
```

**Important**: Replace `your_gemini_api_key_here` with your actual Gemini API key from https://aistudio.google.com/app/apikey

### 5. Create Upload Directory
```powershell
mkdir uploads
```

### 6. Start the Backend Server
```powershell
python run.py
```

The backend will run on `http://localhost:5000`

---

## 🎨 Frontend Setup

### 1. Navigate to Frontend Directory (New Terminal)
```powershell
cd frontend
```

### 2. Install Dependencies
```powershell
npm install
```

### 3. Start Development Server
```powershell
npm run dev
```

The frontend will run on `http://localhost:5173` (or another port if 5173 is busy)

---

## 🚀 Using the Application

### Upload & Analyze a Bill

1. **Open Browser**: Navigate to `http://localhost:5173`
2. **Upload File**: 
   - Drag and drop a medical bill (PDF, JPG, PNG)
   - Or click "Browse Files" to select
3. **Wait for Analysis**: The app will:
   - Extract text from your file
   - Structure the data (patient info, charges, etc.)
   - Analyze for issues and overcharges
   - Generate a human-readable summary
4. **Review Results**: See:
   - Bill details and breakdown
   - Detected issues with severity levels
   - Potential savings
   - Recommendations
   - Email template for disputes

---

## 📁 Project Structure

```
webjam2025/
├── backend/
│   ├── app.py              # Main Flask application with API endpoints
│   ├── models.py           # Database models (Bill, Item)
│   ├── database.py         # SQLAlchemy database configuration
│   ├── text_extractor.py   # PDF and image text extraction
│   ├── llm_service.py      # OpenAI LLM integration
│   ├── requirements.txt    # Python dependencies
│   ├── .env                # Environment variables (create this)
│   ├── .env.example        # Environment template
│   └── uploads/            # Temporary file storage (create this)
│
└── frontend/
    ├── src/
    │   ├── App.jsx                      # Main React component
    │   ├── components/
    │   │   ├── BillUpload.jsx          # File upload with drag-and-drop
    │   │   └── BillAnalysis.jsx        # Analysis results display
    │   ├── index.css                    # Global styles
    │   └── main.jsx                     # React entry point
    └── package.json                     # Node dependencies
```

---

## 🔑 API Endpoints

### POST `/upload`
Upload a medical bill file (PDF, JPG, PNG)
- **Request**: multipart/form-data with 'file' field
- **Response**: Bill ID and extracted text preview

### POST `/analyze/<bill_id>`
Analyze an uploaded bill using AI
- **Response**: Structured data, analysis results, summary, and complaint email

### GET `/bills`
Get all uploaded bills
- **Response**: List of bills with metadata

### GET `/bills/<bill_id>`
Get detailed information for a specific bill
- **Response**: Full bill data including analysis

---

## 🛠️ Troubleshooting

### Tesseract Not Found Error
- **Windows**: Add Tesseract to PATH or set in code:
  ```python
  pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
  ```
- **Mac/Linux**: Ensure `tesseract` command works in terminal

### Gemini API Errors
- Check your API key is valid and from https://aistudio.google.com/app/apikey
- Ensure your Google Cloud project has Gemini API enabled
- Check rate limits if getting quota errors

### CORS Errors
- Ensure backend is running on port 5000
- Check `CORS(app)` is configured in `app.py`

### Port Already in Use
- Backend: Change port in `run.py`
- Frontend: Vite will suggest another port automatically

---

## 🎯 Flow Summary

1. **User Uploads Bill** → Frontend sends file to `/upload`
2. **Text Extraction** → Backend extracts text using pdfplumber/Tesseract
3. **Data Structuring** → LLM extracts patient info, charges, totals
4. **Cost Analysis** → LLM detects overcharges, duplicates, issues
5. **Summary Generation** → LLM creates readable summary + complaint email
6. **Display Results** → Frontend shows analysis with color-coded issues

---

## 📝 Notes

- **File Size Limit**: 16MB per upload
- **Supported Formats**: PDF, JPG, JPEG, PNG
- **Database**: SQLite (app.db) - auto-created on first run
- **LLM Model**: Google Gemini 2.0 Flash (fast and cost-effective)

---

## 🚧 Optional Enhancements

- [ ] User authentication (JWT/Auth0)
- [ ] Bill history tracking
- [ ] Cost visualization charts
- [ ] Insurance plan comparison
- [ ] Email integration for automatic disputes
- [ ] Export reports as PDF

---

## 📞 Support

For issues or questions:
1. Check that all dependencies are installed
2. Verify environment variables are set correctly
3. Check console logs for specific errors
4. Ensure both frontend and backend servers are running

Happy analyzing! 🏥💰
