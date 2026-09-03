# Adaptive Learning Platform

A RAG-based adaptive learning platform for curriculum content, quiz generation, and personalized learning paths. Built for VIT's "Digital Logic Design" course (BAECE102).

## Features

- **RAG Content Engine** — Ingests educational PDFs, generates structured curriculum and quizzes
- **Hybrid Search** — BM25 full-text + vector similarity with RRF fusion
- **Multi-stage Pipeline** — Gatekeeper → Enrichment → Retrieval → Generation → Verification → Citation
- **Interactive Chat** — AI Socratic tutoring with streaming and citation validation
- **Flashcards & Quizzes** — AI-generated study aids
- **Exam Paper Generation** — Configurable with Bloom's taxonomy levels

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16 (JS, CSS custom properties) — `new_frontend/` |
| Backend | FastAPI (Python 3.11) |
| Database | SurrealDB |
| LLM (chat) | Gemini via `generativelanguage.googleapis.com` |
| Embeddings | OpenRouter (NVIDIA Nemotron) |
| Auth | JWT + bcrypt |
| Background | Celery + Redis |
| Containers | Docker Compose (5 services) |

## Prerequisites

### All platforms
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes Docker Compose)
- API keys: [Gemini](https://aistudio.google.com/app/apikey) (chat) + [OpenRouter](https://openrouter.ai/) (embeddings, free tier available)

### For local development (without Docker)

<details>
<summary><b>Windows</b></summary>

```powershell
# Install Python 3.11+
winget install Python.Python.3.11

# Install Node.js 18+
winget install OpenJS.NodeJS.LTS

# Install Make (optional, for make commands)
winget install GnuWin32.Make
```

</details>

<details>
<summary><b>macOS</b></summary>

```bash
# Install Python 3.11+
brew install python@3.11

# Install Node.js 18+
brew install node
```

</details>

<details>
<summary><b>Linux (Debian/Ubuntu)</b></summary>

```bash
# Install Python 3.11+
sudo apt update && sudo apt install -y python3.11 python3.11-venv python3-pip

# Install Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install Make
sudo apt install -y make
```

</details>

<details>
<summary><b>Linux (Fedora/RHEL)</b></summary>

```bash
sudo dnf install -y python3.11 python3.11-virtualenv nodejs make
```

</details>

## Quick Start

### 1. Clone and configure

```bash
git clone <repo-url> && cd adaptive_learning
make setup
```

This copies `backend/.env.example` → `backend/.env`, generates a JWT secret, and installs dependencies.

**Edit `backend/.env`** and add your API keys:
```
GEMINI_API_KEYS=your-key-here
OPENROUTER_API_KEYS=sk-or-v1-your-key-here
```

### 2a. Docker (recommended)

```bash
make docker-up
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8001 |
| SurrealDB | ws://localhost:8000/rpc |

### 2b. Local development

Start only the databases, then run backend and frontend separately:

```bash
# Start SurrealDB + Redis
docker compose up -d surrealdb redis

# Terminal 1 — Backend
cd backend
../backend/venv/bin/uvicorn server:app --reload --port 8001

# Terminal 2 — Frontend
cd new_frontend
npm run dev
```

### Default users

| Email | Password | Role |
|-------|----------|------|
| student@test.com | password123 | student |
| faculty@test.com | password123 | faculty |
| admin@test.com | password123 | admin |

## Services

```
┌──────────┐     ┌──────────┐     ┌───────────┐     ┌───────┐
│ Frontend │────▶│ Backend  │────▶│ SurrealDB │     │ Redis │
│ Next.js  │     │ FastAPI  │     │           │     │       │
│ :3000    │     │ :8001    │     │ :8000     │     │ :6379 │
└──────────┘     └────┬─────┘     └───────────┘     └───┬───┘
                      │                                  │
                      ▼                                  ▼
                ┌──────────┐                      ┌──────────┐
                │ Gemini   │                      │  Worker  │
                │ (chat)   │                      │ (Celery) │
                └──────────┘                      └──────────┘
```

## Project Structure

```
├── backend/
│   ├── app/               # Core modules (rag, query_engine, chunker, routers, auth)
│   ├── server.py          # FastAPI entry point
│   ├── .env               # Your local config (git-ignored)
│   ├── .env.example       # Config template
│   ├── requirements.txt   # Python dependencies
│   └── tests/             # Test suite
├── new_frontend/
│   ├── src/app/           # App Router pages
│   ├── next.config.mjs    # API proxy rewrites
│   └── package.json
├── docs/
│   ├── API.md             # Full API reference
│   └── ARCHITECTURE.md    # System design
├── docker-compose.yml     # 5-service orchestration
├── Makefile               # Common commands
└── scripts/setup.sh       # Idempotent setup script
```

## API Overview

See [`docs/API.md`](docs/API.md) for the full reference.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/healthz` | Health check |
| `POST` | `/auth/login` | Login (returns JWT) |
| `POST` | `/auth/register` | Register user |
| `POST` | `/ingest` | Upload & ingest PDF (faculty/admin) |
| `POST` | `/query` | RAG query → Socratic response |
| `POST` | `/chat` | Interactive chat (streaming) |
| `POST` | `/quiz` | Generate quiz |
| `POST` | `/flashcards` | Generate flashcards |
| `GET` | `/courses` | List courses |
| `POST` | `/paper/generate` | Generate exam paper (faculty/admin) |
| `GET` | `/analytics` | Course-wide analytics (faculty/admin) |
| `GET` | `/analytics/me` | Per-user progress |

## Development Commands

```bash
make setup          # One-time setup (env, deps)
make docker-up      # Build & start all 5 services
make docker-down    # Stop all services
make test           # Run backend + frontend tests
make lint           # Lint backend (ruff) + frontend (eslint)
make clean          # Stop containers, remove venv/node_modules
```

## Environment Variables

See [`backend/.env.example`](backend/.env.example) for all variables with comments.

| Variable | Purpose | Required |
|----------|---------|----------|
| `GEMINI_API_KEYS` | Gemini API keys (comma-separated for rotation) | Yes |
| `OPENROUTER_API_KEYS` | OpenRouter keys for embeddings | Yes |
| `JWT_SECRET` | Auth token signing key | Auto-generated by `make setup` |
| `SURREAL_URL` | SurrealDB WebSocket URL | `ws://localhost:8000/rpc` |
| `SURREAL_NS` / `SURREAL_DB` | SurrealDB namespace/database | Defaults provided |

## Docs

- [`docs/API.md`](docs/API.md) — Full API reference
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — System design and data models
- [`AGENTS.md`](AGENTS.md) — AI agent guide (architecture, commands, gotchas)
