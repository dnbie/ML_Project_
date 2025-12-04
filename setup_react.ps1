param(
    [switch]$Setup,
    [switch]$Run
)

if (-not $Setup -and -not $Run) {
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  .\setup_react.ps1 -Setup    # Setup React + FastAPI version" -ForegroundColor White
    Write-Host "  .\setup_react.ps1 -Run      # Run React + FastAPI version" -ForegroundColor White
    exit
}

$backendPath = "backend"
$frontendPath = "frontend"

if ($Setup) {
    Write-Host "=== Document Intelligence Assistant Setup (React) ===" -ForegroundColor Cyan
    Write-Host ""

    Write-Host "Step 1: Setting up Backend..." -ForegroundColor Yellow

    if (-Not (Test-Path "$backendPath\.env")) {
        if (Test-Path ".env") {
            Copy-Item ".env" "$backendPath\.env"
            Write-Host "Copied .env to backend folder" -ForegroundColor Green
        } else {
            Write-Host "WARNING: .env file not found. Please create it in backend folder" -ForegroundColor Yellow
        }
    }

    if (-Not (Test-Path "$backendPath\venv")) {
        Write-Host "Creating backend virtual environment..." -ForegroundColor Yellow
        Set-Location $backendPath
        python -m venv venv
        Set-Location ..
        Write-Host "Backend venv created" -ForegroundColor Green
    }

    Write-Host "Activating backend venv and installing dependencies..." -ForegroundColor Yellow
    Set-Location $backendPath
    & ".\venv\Scripts\Activate.ps1"
    pip install -r requirements.txt
    Set-Location ..

    Write-Host ""
    Write-Host "Step 2: Setting up Frontend..." -ForegroundColor Yellow

    if (-Not (Test-Path "$frontendPath\node_modules")) {
        Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
        Set-Location $frontendPath
        npm install
        Set-Location ..
        Write-Host "Frontend dependencies installed" -ForegroundColor Green
    }

    Write-Host ""
    Write-Host "=== Setup Complete! ===" -ForegroundColor Green
    Write-Host "Run: .\setup_react.ps1 -Run" -ForegroundColor Cyan
}

if ($Run) {
    Write-Host "=== Starting Document Intelligence Assistant (React) ===" -ForegroundColor Cyan
    Write-Host ""

    Write-Host "Starting Backend Server..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\$backendPath'; .\venv\Scripts\Activate.ps1; python app.py"

    Start-Sleep -Seconds 3

    Write-Host "Starting Frontend..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\$frontendPath'; npm start"

    Write-Host ""
    Write-Host "=== Application Starting ===" -ForegroundColor Green
    Write-Host "Backend: http://localhost:8000" -ForegroundColor White
    Write-Host "Frontend: http://localhost:3000" -ForegroundColor White
    Write-Host ""
    Write-Host "Two terminal windows will open. Close them to stop the application." -ForegroundColor Yellow
}
