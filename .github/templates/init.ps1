# Long-Running Agent Environment Initialization Script (PowerShell)
# This script sets up the development environment for agent sessions

$ErrorActionPreference = "Stop"  # Exit on any error

# Configuration - adjust these for your project
$DEV_PORT = 3000  # Change to match your dev server port

Write-Host "🚀 Starting development environment..." -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# 1. Check prerequisites
Write-Host "`n📋 Checking prerequisites..." -ForegroundColor Yellow

# Node.js project:
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Node.js is required but not installed" -ForegroundColor Red
    exit 1
}
Write-Host "   ✅ Node.js $(node -v)" -ForegroundColor Green

# Python project:
# if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
#     Write-Host "❌ Python is required but not installed" -ForegroundColor Red
#     exit 1
# }
# Write-Host "   ✅ Python $(python --version)" -ForegroundColor Green

# 2. Kill any stale dev servers on target port
Write-Host "`n🔍 Checking for stale processes on port $DEV_PORT..." -ForegroundColor Yellow
$staleProcesses = Get-NetTCPConnection -LocalPort $DEV_PORT -ErrorAction SilentlyContinue | 
Select-Object -ExpandProperty OwningProcess -Unique
if ($staleProcesses) {
    foreach ($pid in $staleProcesses) {
        Write-Host "  Killing stale process PID: $pid" -ForegroundColor Yellow
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 1
    Write-Host "   ✅ Stale processes cleaned up" -ForegroundColor Green
}
else {
    Write-Host "   ✅ No stale processes found" -ForegroundColor Green
}

# 3. Install dependencies
Write-Host "`n📦 Installing dependencies..." -ForegroundColor Yellow

# Node.js project:
if (-not (Test-Path "node_modules")) {
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Dependency installation failed!" -ForegroundColor Red
        exit 1
    }
}
else {
    Write-Host "   ✅ Dependencies already installed" -ForegroundColor Green
}

# Python project:
# pip install -r requirements.txt

# 4. Start development server in BACKGROUND using Start-Job
Write-Host "`n🖥️  Starting development server in background..." -ForegroundColor Yellow

# Node.js project:
$devJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    npm run dev 2>&1
}
Write-Host "   Started dev server as background job (Job ID: $($devJob.Id))" -ForegroundColor Gray

# 5. Wait for server to be ready (with timeout)
Write-Host "`n⏳ Waiting for server to be ready..." -ForegroundColor Yellow
$maxAttempts = 30
$attempt = 0
$serverReady = $false

while ($attempt -lt $maxAttempts -and -not $serverReady) {
    Start-Sleep -Seconds 1
    $attempt++
    try {
        $connection = Test-NetConnection -ComputerName localhost -Port $DEV_PORT -WarningAction SilentlyContinue
        if ($connection.TcpTestSucceeded) {
            $serverReady = $true
        }
    }
    catch {
        # Continue waiting
    }
}

if (-not $serverReady) {
    Write-Host "❌ Server failed to start within 30 seconds!" -ForegroundColor Red
    Write-Host "   Checking job output..." -ForegroundColor Yellow
    Receive-Job -Id $devJob.Id
    exit 1
}

Write-Host "   ✅ Dev server ready on port $DEV_PORT" -ForegroundColor Green

# 6. Health check
Write-Host "`n🏥 Running health check..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:$DEV_PORT" -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "   ✅ Health check passed (HTTP 200)" -ForegroundColor Green
    }
}
catch {
    Write-Host "   ❌ Health check failed: $_" -ForegroundColor Red
    exit 1
}

# 7. Success message
Write-Host "`n================================================" -ForegroundColor Cyan
Write-Host "✅ Environment ready!" -ForegroundColor Green
Write-Host ""
Write-Host "📍 Server running at: http://localhost:$DEV_PORT" -ForegroundColor White
Write-Host "📖 To view output: Receive-Job -Id $($devJob.Id)" -ForegroundColor Gray
Write-Host "📖 To stop: Stop-Job -Id $($devJob.Id); Remove-Job -Id $($devJob.Id)" -ForegroundColor Gray
Write-Host ""
Write-Host "🎯 Ready for coding session." -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
