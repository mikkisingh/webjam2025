# Quick Setup for Gemini API
# Run this after getting your Gemini API key

Write-Host "================================" -ForegroundColor Cyan
Write-Host "   MediCheck - Gemini Setup    " -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

$backendPath = Join-Path $PSScriptRoot "backend"
$envPath = Join-Path $backendPath ".env"
$envExamplePath = Join-Path $backendPath ".env.example"

# Check if .env already exists
if (Test-Path $envPath) {
    Write-Host "⚠️  .env file already exists" -ForegroundColor Yellow
    $overwrite = Read-Host "Do you want to reconfigure? (y/n)"
    if ($overwrite -ne "y") {
        Write-Host "Keeping existing configuration." -ForegroundColor Gray
        exit 0
    }
}

Write-Host "Setting up Gemini API configuration..." -ForegroundColor Green
Write-Host ""

# Get API key from user
Write-Host "Get your Gemini API key from: https://aistudio.google.com/app/apikey" -ForegroundColor White
Write-Host ""
$apiKey = Read-Host "Enter your Gemini API key"

if ([string]::IsNullOrWhiteSpace($apiKey)) {
    Write-Host "❌ No API key provided. Exiting." -ForegroundColor Red
    exit 1
}

# Create .env file
$envContent = @"
# Google Gemini API Key for LLM analysis
# Get your API key from: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=$apiKey

# Upload folder for temporary file storage
UPLOAD_FOLDER=uploads
"@

$envContent | Out-File -FilePath $envPath -Encoding UTF8

Write-Host ""
Write-Host "✓ .env file created successfully!" -ForegroundColor Green
Write-Host ""

# Install dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
Push-Location $backendPath
try {
    python -m pip install -r requirements.txt --quiet
    Write-Host "✓ Dependencies installed!" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Error installing dependencies. Run manually:" -ForegroundColor Yellow
    Write-Host "  cd backend" -ForegroundColor Gray
    Write-Host "  pip install -r requirements.txt" -ForegroundColor Gray
}
Pop-Location

Write-Host ""

# Create uploads directory if it doesn't exist
$uploadsPath = Join-Path $backendPath "uploads"
if (-not (Test-Path $uploadsPath)) {
    New-Item -ItemType Directory -Path $uploadsPath | Out-Null
    Write-Host "✓ Created uploads directory" -ForegroundColor Green
}

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "   Setup Complete!              " -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. cd backend" -ForegroundColor Gray
Write-Host "  2. python test_setup.py    (verify setup)" -ForegroundColor Gray
Write-Host "  3. python run.py           (start backend)" -ForegroundColor Gray
Write-Host ""
Write-Host "Then in another terminal:" -ForegroundColor White
Write-Host "  1. cd frontend" -ForegroundColor Gray
Write-Host "  2. npm install" -ForegroundColor Gray
Write-Host "  3. npm run dev" -ForegroundColor Gray
Write-Host ""
Write-Host "Or use: .\start.ps1 to start both servers" -ForegroundColor Cyan
Write-Host ""
