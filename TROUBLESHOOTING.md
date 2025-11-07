# MediCheck - Troubleshooting Guide

Common issues and solutions when setting up and running MediCheck.

---

## Backend Issues

### ❌ ImportError: No module named 'pdfplumber' (or other packages)

**Solution:**
```powershell
cd backend
pip install -r requirements.txt
```

If still failing, try upgrading pip first:
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

### ❌ TesseractNotFoundError

**Problem:** Tesseract OCR is not installed or not in PATH.

**Windows Solution:**
1. Download Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
2. Install to default location: `C:\Program Files\Tesseract-OCR`
3. Add to PATH or configure in code:
   - Edit `text_extractor.py`
   - Add at top: `pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'`

**Mac Solution:**
```bash
brew install tesseract
```

**Linux Solution:**
```bash
sudo apt-get install tesseract-ocr
```

**Verify Installation:**
```powershell
tesseract --version
```

---

### ❌ OpenAI API Error: Authentication Error

**Problem:** OPENAI_API_KEY is missing or invalid.

**Solution:**
1. Get API key from https://platform.openai.com/api-keys
2. Edit `backend/.env`:
   ```env
   OPENAI_API_KEY=sk-your-actual-key-here
   ```
3. Restart the backend server

---

### ❌ OpenAI API Error: Rate Limit / 429 Error

**Problem:** Too many requests or insufficient credits.

**Solution:**
1. Check your OpenAI account usage: https://platform.openai.com/usage
2. Add credits if needed
3. Wait a moment and try again
4. Consider implementing rate limiting in production

---

### ❌ Port 5000 Already in Use

**Problem:** Another application is using port 5000.

**Solution 1 - Stop other app:**
```powershell
# Find process using port 5000
netstat -ano | findstr :5000

# Kill process (replace PID with actual number)
taskkill /PID <PID> /F
```

**Solution 2 - Use different port:**
Edit `backend/run.py`:
```python
app.run(debug=True, port=5001)  # Change to 5001
```

Then update frontend API calls in components to use `http://localhost:5001`

---

### ❌ Database Error: Unable to open database file

**Problem:** Permissions issue with SQLite database.

**Solution:**
```powershell
cd backend
Remove-Item app.db -Force  # Delete old database
python run.py  # Will create new database
```

---

### ❌ File Upload Error: File too large

**Problem:** File exceeds 16MB limit.

**Solution:** Increase limit in `backend/app.py`:
```python
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB
```

---

## Frontend Issues

### ❌ npm install fails

**Problem:** Node modules installation error.

**Solution:**
```powershell
cd frontend
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
npm install
```

---

### ❌ CORS Error: Access-Control-Allow-Origin

**Problem:** Frontend can't connect to backend.

**Symptoms:**
```
Access to fetch at 'http://localhost:5000/upload' from origin 'http://localhost:5173' 
has been blocked by CORS policy
```

**Solution:**
1. Verify backend is running: http://localhost:5000
2. Check `backend/app.py` has:
   ```python
   from flask_cors import CORS
   CORS(app)
   ```
3. Restart backend server

---

### ❌ Vite Port Already in Use

**Problem:** Port 5173 is occupied.

**Solution:** Vite will automatically suggest another port (5174, 5175, etc.). 
Just press 'y' to accept the alternative port.

Or specify a port in `frontend/vite.config.js`:
```javascript
export default {
  server: {
    port: 3000
  }
}
```

---

### ❌ Component not rendering / Blank page

**Problem:** JavaScript error in browser.

**Solution:**
1. Open browser DevTools (F12)
2. Check Console tab for errors
3. Common issues:
   - Missing import statements
   - Typos in component names
   - API endpoint URL mismatch

---

### ❌ File upload not working

**Problem:** Upload button does nothing or shows error.

**Checklist:**
1. ✓ Backend is running on port 5000
2. ✓ File type is PDF, JPG, or PNG
3. ✓ File size is under 16MB
4. ✓ No CORS errors in browser console
5. ✓ Network tab shows request to http://localhost:5000/upload

**Debug:**
Open browser DevTools → Network tab → Try upload → Check:
- Request URL should be `http://localhost:5000/upload`
- Status should be 201 or 200
- Response should have bill ID

---

## Analysis Issues

### ❌ Analysis stuck on "Analyzing..."

**Problem:** LLM request is taking too long or failed silently.

**Solution:**
1. Check backend terminal for errors
2. Verify OpenAI API key is valid
3. Check internet connection
4. Try with smaller/simpler bill first

**Timeout fix** in `backend/llm_service.py`:
```python
response = self.client.chat.completions.create(
    model=self.model,
    messages=[...],
    timeout=60  # Add timeout parameter
)
```

---

### ❌ Poor text extraction quality

**Problem:** OCR returns gibberish or incomplete text.

**Solutions:**
- **For images**: Use higher resolution (300 DPI minimum)
- **For PDFs**: Ensure PDF has text layer (not scanned image)
- **Image quality**: Good lighting, no blur, straight alignment
- **Tesseract**: Update to latest version

---

### ❌ Analysis results are inaccurate

**Problem:** LLM misidentifies charges or misses issues.

**Reasons:**
1. Poor text extraction quality (see above)
2. Unusual bill format
3. Model limitations

**Improvements:**
- Use clearer bill scans
- Try PDF version if using image
- Manually verify critical information
- Consider fine-tuning prompts in `llm_service.py`

---

## General Issues

### ❌ "Module not found" errors after git pull

**Problem:** New dependencies added.

**Solution:**
```powershell
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

---

### ❌ Changes not reflecting

**Problem:** Code changes don't appear in running app.

**Solution:**
- **Backend**: Stop server (Ctrl+C), restart with `python run.py`
- **Frontend**: Vite hot-reload should work automatically
  - If not: Stop (Ctrl+C), clear cache: `npm run dev -- --force`

---

## Testing Setup

### Run Setup Test

Before starting, verify everything is configured:

```powershell
cd backend
python test_setup.py
```

This will check:
- ✓ All Python packages installed
- ✓ Tesseract OCR available
- ✓ Environment variables configured
- ✓ Required directories exist

---

## Getting Help

If you're still stuck:

1. **Check Logs:**
   - Backend: Terminal running `python run.py`
   - Frontend: Terminal running `npm run dev`
   - Browser: DevTools Console (F12)

2. **Verify Versions:**
   ```powershell
   python --version  # Should be 3.8+
   node --version    # Should be 16+
   pip --version
   npm --version
   ```

3. **Fresh Start:**
   ```powershell
   # Backend
   cd backend
   Remove-Item -Recurse venv, __pycache__, *.db
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   
   # Frontend
   cd frontend
   Remove-Item -Recurse node_modules, dist
   npm install
   ```

4. **Documentation:**
   - [SETUP.md](SETUP.md) - Installation guide
   - [README.md](README.md) - Project overview
   - Backend API docs in `backend/README.md`

---

## Common Error Messages

| Error | Meaning | Fix |
|-------|---------|-----|
| `ModuleNotFoundError` | Missing Python package | `pip install -r requirements.txt` |
| `TesseractNotFoundError` | OCR not installed | Install Tesseract OCR |
| `AuthenticationError` | Invalid API key | Check `.env` file |
| `CORS policy` | Backend not running | Start backend server |
| `ENOENT` | File/folder missing | Create required directories |
| `EADDRINUSE` | Port in use | Change port or kill process |

---

**Still having issues?** Check the specific error message in your terminal or browser console for more details.
