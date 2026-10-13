# ZED VISION - Windows PowerShell Launch Script
Write-Host "=====================================================" -ForegroundColor Red
Write-Host "  ZED VISION: Occlusion Intelligence MOT Engine     " -ForegroundColor White
Write-Host "  PS-2: Dense Occlusion Multi-Object Tracking       " -ForegroundColor Gray
Write-Host "=====================================================" -ForegroundColor Red

# Configure Node and Cache environment
$nodePath = "C:\Users\DELL\AppData\Local\Programs\node-portable\node-v22.20.0-win-x64"
if (Test-Path $nodePath) {
    $env:PATH = "$nodePath;$env:PATH"
}
$env:TEMP = "D:\temp"
$env:TMP = "D:\temp"

Write-Host "`n[1/3] Checking environment & test suite..." -ForegroundColor Cyan
python -m pytest backend/tests/ -q
if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARNING] Some tests encountered issues. Review test logs." -ForegroundColor Yellow
} else {
    Write-Host "[OK] All 21 tracking and OIE unit tests passed." -ForegroundColor Green
}

Write-Host "`n[2/3] Checking synthetic demo video..." -ForegroundColor Cyan
python -c "from backend.app.services.session_manager import SessionManager; SessionManager()._ensure_sample_demo_video(); print('[OK] Demo transit gate sequence ready.')"

Write-Host "`n[3/3] Starting ZED VISION Unified Web Server on port 8080..." -ForegroundColor Cyan
Write-Host "Dashboard URL: http://127.0.0.1:8080" -ForegroundColor Green
Write-Host "API Health:    http://127.0.0.1:8080/api/health" -ForegroundColor Green
Write-Host "Press Ctrl+C to terminate the server.`n" -ForegroundColor Gray

python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8080
