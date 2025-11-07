# MediCheck - Quick Start Script
# This script starts both the backend and frontend servers

Write-Host "================================" -ForegroundColor Cyan
Write-Host "   MediCheck - Starting...     " -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

# Check if Node is installed
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✓ Node.js found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Node.js not found. Please install Node.js 16+" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Starting backend server..." -ForegroundColor Yellow

# Start backend in new window
$backendPath = Join-Path $PSScriptRoot "backend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$backendPath'; python run.py"

Write-Host "✓ Backend started in new window" -ForegroundColor Green
Write-Host ""

# Wait a moment for backend to initialize
Start-Sleep -Seconds 3

Write-Host "Starting frontend server..." -ForegroundColor Yellow

# Start frontend in new window
$frontendPath = Join-Path $PSScriptRoot "frontend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$frontendPath'; npm run dev"

Write-Host "✓ Frontend started in new window" -ForegroundColor Green
Write-Host ""

Write-Host "================================" -ForegroundColor Cyan
Write-Host "   MediCheck is running!       " -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend:  http://localhost:5000" -ForegroundColor White
Write-Host "Frontend: http://localhost:5173" -ForegroundColor White
Write-Host ""
Write-Host "Close the terminal windows to stop the servers." -ForegroundColor Gray
Write-Host ""

# Keep this window open
Write-Host "Press any key to exit this window (servers will keep running)..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
