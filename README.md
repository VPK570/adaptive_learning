# Adaptive Learning Platform (MVP)

A modular adaptive learning platform featuring a RAG-based backend for curriculum content, quiz generation, and personalized learning paths.

## Features
- **RAG-based Content Engine**: Ingests educational PDFs and generates structured curriculum/quizzes.
- **Personalized Learning**: Tracks student progress and adapts based on performance.
- **Interactive Chat**: AI-powered tutoring with citation support.

## Tech Stack
- **Backend**: FastAPI
- **Frontend**: Next.js (TypeScript)
- **Vector Store**: ChromaDB
- **LLM Provider**: OpenRouter

## Setup
1. Clone the repository.
2. Run the setup script for your platform in the `setup/` directory:
   - Linux/macOS: `bash setup/setup.sh`
   - Windows: `setup\setup.ps1` or `setup\setup.bat`
3. Follow the prompts to configure the required environment variables (`.env`).

## Running the Application
- **Backend**: Navigate to `backend/`, install requirements, and run `uvicorn main:app --reload`.
- **Frontend**: Navigate to `frontend/`, install dependencies (`npm install`), and run `npm run dev`.

## Project Structure
- `backend/`: FastAPI application core.
- `frontend/`: Next.js web application.
- `docs/`: Documentation and API specifications.
- `sample_data/`: Example JSON curricula and quizzes.
- `setup/`: Platform-specific setup scripts.

## MVP Limitations
- Currently expects a single PDF/curriculum file for initial ingestion.
- Authentication is mocked for the MVP.
- Vector store is local (ChromaDB).

## Contribution
Contributions are welcome! Please refer to `CONTRIBUTING.md` for guidelines.
