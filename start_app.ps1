Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "   SMART ATTENDANCE SYSTEM - FACIAL RECOGNITION & ATTENFACE ANALYTICS" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

$CurrentDir = $PSScriptRoot

Write-Host "[1/2] Launching FastAPI Backend on http://127.0.0.1:8000 ..." -ForegroundColor Green
Start-Process -FilePath "cmd.exe" -ArgumentList "/k cd /d `"$CurrentDir`" && .venv\Scripts\python.exe run_server.py"

Write-Host "[2/2] Launching React Vite Frontend on http://localhost:5173 ..." -ForegroundColor Green
Start-Process -FilePath "cmd.exe" -ArgumentList "/k cd /d `"$CurrentDir\frontend`" && npm.cmd run dev"

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host " System is running!" -ForegroundColor Green
Write-Host " - Frontend Dashboard: http://localhost:5173" -ForegroundColor Yellow
Write-Host " - Interactive Swagger API: http://127.0.0.1:8000/docs" -ForegroundColor Yellow
Write-Host "======================================================================" -ForegroundColor Cyan
