# ==============================================================================
# Credit Risk System - Windows PowerShell Service Launcher
# ==============================================================================

Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "   🚀 CREDIT RISK SYSTEM - POWERSHELL LAUNCHER     " -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

# 1. Activate Virtual Environment
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "✓ Activating Python virtual environment (.venv)..." -ForegroundColor Green
    & .venv\Scripts\Activate.ps1
} elseif (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "✓ Activating Python virtual environment (venv)..." -ForegroundColor Green
    & venv\Scripts\Activate.ps1
} else {
    Write-Host "⚠ Warning: Virtual environment not found. Using global Python." -ForegroundColor Yellow
}

# 2. Display Menu
Write-Host "`nSelect an action to run:" -ForegroundColor Cyan
Write-Host "  1) Run ALL (API Server + Web App Frontend in separate windows)"
Write-Host "  2) Run API Server only (FastAPI on http://localhost:8000)"
Write-Host "  3) Run Web App Frontend only (Vite on http://localhost:5173)"
Write-Host "  4) Run Data Pipeline ETL (Extract & Transform)"
Write-Host "  5) Run ML Training Pipeline (Credit Risk)"
Write-Host "  q) Quit`n"

$choice = Read-Host "Enter choice [1-5 or q]"

switch ($choice) {
    "1" {
        Write-Host "`nStarting API Server and Web App in new PowerShell windows..." -ForegroundColor Green
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot'; & .venv\Scripts\Activate.ps1; python -m services.api_server.app.main"
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot\services\web_app'; npm run dev"
        Write-Host "✓ API Server docs available at: http://localhost:8000/docs" -ForegroundColor Cyan
        Write-Host "✓ Web App UI available at:     http://localhost:5173" -ForegroundColor Cyan
    }
    "2" {
        Write-Host "`nStarting FastAPI API Server..." -ForegroundColor Green
        python -m services.api_server.app.main
    }
    "3" {
        Write-Host "`nStarting Web App Frontend..." -ForegroundColor Green
        Set-Location "$PSScriptRoot\services\web_app"
        npm run dev
    }
    "4" {
        Write-Host "`nExecuting Data Pipeline ETL (--skip-db)..." -ForegroundColor Green
        python -m services.data_pipeline.main --skip-db
    }
    "5" {
        Write-Host "`nExecuting ML Training Pipeline..." -ForegroundColor Green
        python -m services.ml_engine.src.machine_learning.pipeline --task credit_risk
    }
    "q" {
        Write-Host "Exiting." -ForegroundColor Green
        exit 0
    }
    Default {
        Write-Host "Invalid choice. Exiting." -ForegroundColor Red
    }
}
