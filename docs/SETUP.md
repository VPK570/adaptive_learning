# Setup Guide

This guide helps you set up the project locally for development and experimentation.

## Prerequisites
- Python 3.10+
- Node.js 18+
- An [OpenRouter API key](https://openrouter.ai/)

## Installation
1. Clone the repo and navigate into the folder.
2. Configure your environment:
   ```bash
   cp .env.example .env && cp .env backend/.env
   # Add your OPENROUTER_API_KEY to the .env file
   ```
3. Run the setup scripts from the `setup/` directory:
   - **Linux/macOS**: `./setup/setup.sh`
   - **Windows**: Use `setup/setup.bat` or `setup/setup.ps1`

## Running the Project
- The backend API runs on port 8001 by default.
- The frontend will start locally (usually on port 3000).

## Troubleshooting
- **Virtual Environment**: Ensure you are using the virtual environment created in `backend/venv/` when running backend tests or scripts manually.
- **API Keys**: Ensure `OPENROUTER_API_KEY` is set in the backend `.env`.
- **Permissions**: If scripts fail to execute, ensure they have execute permissions (`chmod +x setup/*.sh`).
