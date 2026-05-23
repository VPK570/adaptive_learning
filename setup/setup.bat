@echo off
setlocal
echo --- Setup: Adaptive Learning Platform ---

:: Verify Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python not found.
    exit /b 1
)

:: Verify Node
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Node.js not found.
    exit /b 1
)

:: Setup Backend
cd backend
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
cd ..

:: Setup Frontend
cd frontend
call npm install
cd ..

:: Config
if not exist backend\.env (
    copy backend\.env.example backend\.env
    echo Enter your OpenRouter API Key:
    set /p API_KEY=
    powershell -Command "(Get-Content backend\.env) -replace 'your_api_key_here', '%API_KEY%' | Set-Content backend\.env"
)

echo --- Setup Complete ---
echo To start:
echo 1. Backend: cd backend && call venv\Scripts\activate && python main.py
echo 2. Frontend: cd frontend && npm run dev
