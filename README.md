# Adaptive Learning Platform (MVP)

A modular adaptive learning platform featuring a RAG-based backend for curriculum content, quiz generation, and personalized learning paths. Targets VIT's "Digital Logic Design" course (BAECE102).

## Features
- **RAG-based Content Engine**: Ingests educational PDFs and generates structured curriculum/quizzes
- **Hybrid Search**: BM25 full-text + vector similarity with RRF fusion
- **Multi-stage Pipeline**: Gatekeeper → Enrichment → Retrieval → Generation → Verification → Citation enforcement
- **Interactive Chat**: AI-powered Socratic tutoring with streaming support and citation validation
- **Flashcards & Quizzes**: AI-generated study aids
- **Exam Paper Generation**: Configurable with Bloom's taxonomy levels

## Tech Stack
| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16 (JavaScript, plain CSS custom properties) — `new_frontend/` |
| Backend | FastAPI (Python) |
| Primary DB | SurrealDB (persistent file mode in Docker) |
| LLM Provider | OpenRouter (free tier: Nemotron VL) |
| Auth | JWT + bcrypt (enforced on all routes via middleware + role-based guards) |
| Containerization | Docker Compose (3 services) |

## Project Structure
```
├── backend/               # FastAPI application
│   ├── app/               # Core modules (rag, query_engine, chunker, routers, auth, etc.)
│   ├── server.py          # Server entry point
│   └── tests/             # Test suite
├── new_frontend/          # Next.js 16 frontend
│   └── src/app/           # App Router pages
├── docs/
│   └── API.md             # API reference
├── .env.example           # Environment variable template
└── docker-compose.yml     # Orchestration (backend + SurrealDB + frontend)
```

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- An [OpenRouter API key](https://openrouter.ai/)

### Local Setup
```bash
cp .env.example .env
# Add your OPENROUTER_API_KEY and generate a JWT_SECRET to .env

# Start the backend
cd backend && uvicorn server:app --reload --port 8001

# In another terminal, start the frontend
cd new_frontend && npm install && npm run dev
```

### Docker
```bash
docker compose up --build
```

## Architecture

### Services
```
┌──────────┐     ┌──────────┐     ┌───────────┐
│ Frontend │────▶│ Backend  │────▶│ SurrealDB │
│ Next.js  │     │ FastAPI  │     │ (file)    │
│ :3000    │     │ :8001    │     │ :8000     │
└──────────┘     └────┬─────┘     └───────────┘
                       │
                       ▼
                 ┌──────────┐
                 │ OpenRouter│
                 │ (LLM +   │
                 │ Embed)   │
                 └──────────┘
```

### RAG Pipeline Stages
1. **Gatekeeper** — LLM-based relevance check
2. **Enrichment** — Context assembly
3. **Retrieval** — Hybrid BM25 + vector search with RRF
4. **Generation** — Socratic response via configurable LLM
5. **Verification** — LLM-based grounding check
6. **Citation Enforcement** — Multi-pass citation validation

## API Overview
See `docs/API.md` for the full API reference. Key endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/ingest` | Upload & ingest PDF (faculty/admin) |
| `POST` | `/query` | Full RAG query → Socratic response |
| `POST` | `/quiz` | Generate quiz |
| `POST` | `/flashcards` | Generate flashcards |
| `GET` | `/courses` | List courses |
| `POST` | `/auth/login` | Login (returns JWT) |
| `POST` | `/auth/register` | Register user |
| `POST` | `/generate-paper` | Generate exam paper (faculty/admin) |
| `GET` | `/analytics` | Course-wide analytics (faculty/admin) |
| `GET` | `/analytics/me` | Per-user progress data |
