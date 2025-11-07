"""
Simple test to verify backend setup and dependencies.
Run this before starting the application.
"""
import sys

def test_imports():
    """Test if all required packages are installed."""
    print("Testing imports...")
    
    required_packages = {
        'flask': 'Flask',
        'flask_cors': 'Flask-CORS',
        'sqlalchemy': 'SQLAlchemy',
        'pdfplumber': 'pdfplumber',
        'PIL': 'Pillow',
        'google.generativeai': 'google-generativeai',
        'dotenv': 'python-dotenv'
    }
    
    missing_packages = []
    
    for package, name in required_packages.items():
        try:
            __import__(package)
            print(f"✓ {name}")
        except ImportError:
            print(f"✗ {name} - NOT INSTALLED")
            missing_packages.append(name)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("\n✓ All packages installed!")
    return True

def test_tesseract():
    """Test if Tesseract OCR is available."""
    print("\nTesting Tesseract OCR...")
    try:
        import pytesseract
        version = pytesseract.get_tesseract_version()
        print(f"✓ Tesseract OCR version: {version}")
        return True
    except Exception as e:
        print(f"✗ Tesseract OCR not found or not configured")
        print(f"  Error: {str(e)}")
        print("  Install Tesseract:")
        print("  - Windows: https://github.com/UB-Mannheim/tesseract/wiki")
        print("  - Mac: brew install tesseract")
        print("  - Linux: sudo apt-get install tesseract-ocr")
        return False

def test_env():
    """Test if environment variables are configured."""
    print("\nTesting environment configuration...")
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    api_key = os.getenv('GEMINI_API_KEY')
    if api_key and api_key != 'your_gemini_api_key_here' and api_key != 'your_openai_api_key_here':
        print("✓ GEMINI_API_KEY is set")
        return True
    else:
        print("✗ GEMINI_API_KEY not configured")
        print("  1. Copy .env.example to .env")
        print("  2. Add your Gemini API key from https://aistudio.google.com/app/apikey")
        return False

def test_directories():
    """Test if required directories exist."""
    print("\nTesting directories...")
    import os
    
    upload_dir = os.getenv('UPLOAD_FOLDER', 'uploads')
    
    if os.path.exists(upload_dir):
        print(f"✓ Upload directory exists: {upload_dir}")
        return True
    else:
        print(f"✗ Upload directory missing: {upload_dir}")
        print(f"  Create it: mkdir {upload_dir}")
        return False

def main():
    """Run all tests."""
    print("=" * 50)
    print("MediCheck Backend - Setup Test")
    print("=" * 50)
    
    results = []
    results.append(test_imports())
    results.append(test_tesseract())
    results.append(test_env())
    results.append(test_directories())
    
    print("\n" + "=" * 50)
    if all(results):
        print("✅ All tests passed! Backend is ready to run.")
        print("\nStart the server with: python run.py")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        print("\nRefer to SETUP.md for detailed instructions.")
    print("=" * 50)
    
    return 0 if all(results) else 1

if __name__ == "__main__":
    sys.exit(main())
