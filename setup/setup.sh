#!/bin/bash
set -e

echo "--- Setup: Adaptive Learning Platform ---"

# Verify Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 not found."
    exit 1
fi

PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if (( $(echo "$PY_VER < 3.10" | bc -l) )); then
    echo "Error: Python 3.10+ required. Found $PY_VER"
    exit 1
fi

# Verify Node
if ! command -v node &> /dev/null; then
    echo "Error: Node.js not found."
    exit 1
fi

NODE_VER=$(node -v | cut -d 'v' -f 2 | cut -d '.' -f 1)
if [ "$NODE_VER" -lt 18 ]; then
    echo "Error: Node 18+ required. Found $(node -v)"
    exit 1
fi

# Setup Backend
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cd ..

# Setup Frontend
cd frontend
npm install
cd ..

# Config
if [ ! -f "backend/.env" ]; then
    cp backend/.env.example backend/.env
    echo "Enter your OpenRouter API Key:"
    read -s API_KEY
    sed -i "s/your_api_key_here/$API_KEY/" backend/.env
    echo ".env created."
fi

echo "--- Setup Complete ---"
echo "To start:"
echo "1. Backend: cd backend && source venv/bin/activate && python main.py"
echo "2. Frontend: cd frontend && npm run dev"
