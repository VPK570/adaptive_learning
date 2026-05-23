Write-Host "--- Setup: Adaptive Learning Platform ---" -ForegroundColor Cyan

# Verify Python
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Python not found." -ForegroundColor Red
    exit 1
}

# Verify Node
if (-not (Get-Command "node" -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Node.js not found." -ForegroundColor Red
    exit 1
}

# Setup Backend
Set-Location backend
if (-not (Test-Path "venv")) {
    python -m venv venv
}
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Set-Location ..

# Setup Frontend
Set-Location frontend
npm install
Set-Location ..

# Config
if (-not (Test-Path "backend\.env")) {
    Copy-Item "backend\.env.example" "backend\.env"
    $API_KEY = Read-Host -Prompt "Enter OpenRouter API Key"
    (Get-Content backend\.env) -replace 'your_api_key_here', $API_KEY | Set-Content backend\.env
}

Write-Host "--- Setup Complete ---" -ForegroundColor Green
Write-Host "1. Backend: cd backend; .\venv\Scripts\Activate.ps1; python main.py"
Write-Host "2. Frontend: cd frontend; npm run dev"
