# Adaptive Learning Platform (MVP)

## ⚠️ SECURITY WARNING

**Hardcoded credentials in `docker-compose.yml`:**
- An OpenRouter API key and JWT secret are hardcoded in `docker-compose.yml:25-26`. Anyone with repo access can use them. **Rotate immediately.**
- See `REPOSITORY_AUDIT_REPORT.md` for the full security audit (score: 2/10).

---

A modular adaptive learning platform featuring a RAG-based backend for curriculum content, quiz generation, and personalized learning paths. Targets VIT's "Digital Logic Design" course (BAECE102).

## Features
- **RAG-based Content Engine**: Ingests educational PDFs and generates structured curriculum/quizzes
- **Multimodal RAG**: Native image embedding (Nemotron VL) with separate text/image ChromaDB collections
- **Hybrid Search**: BM25 full-text + vector similarity with RRF fusion
- **Multi-stage Pipeline**: Gatekeeper → Enrichment → Retrieval → Generation → Verification → Citation enforcement
- **Interactive Chat**: AI-powered Socratic tutoring with streaming support and citation validation
- **Flashcards & Quizzes**: AI-generated study aids
- **Exam Paper Generation**: Configurable with Bloom's taxonomy levels

## Tech Stack
| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python) |
| Frontend (production) | Next.js 16 (TypeScript, Tailwind CSS v4) — `frontend/` |
| Frontend (experimental) | Next.js 16 (JavaScript, plain CSS custom properties) — `new_frontend/` |
| Vector Store | ChromaDB (text_chunks + image_chunks collections) |
| Primary DB | SurrealDB (persistent file mode in Docker) |
| LLM Provider | OpenRouter (free tier: Ring 2.6, Nemotron VL) |
| Containerization | Docker Compose (3 active services + 1 dead) |

> **Note:** Postgres (`pgvector/pgvector:pg16`) is defined in `docker-compose.yml` but **no code connects to it**. It is dead infrastructure.

## Project Structure
```
├── backend/               # FastAPI application
│   ├── app/               # Core modules (rag, query_engine, chunker, routers, etc.)
│   ├── server.py          # Server entry point (568 lines — needs refactoring)
│   ├── scripts/           # CLI utilities
│   └── tests/             # Test suite
├── frontend/              # Next.js 16 + Tailwind CSS v4 (dockerized, production-ready)
│   ├── app/               # App Router pages (chat, quiz, flashcards, etc.)
│   └── Dockerfile         # Docker build for frontend service
├── new_frontend/          # Experimental Next.js 16 frontend (plain CSS, mock-data based)
│   ├── src/app/           # App Router pages (dashboard, chat, quiz, flashcards, etc.)
│   └── AGENTS.md          # Agent configuration for this frontend
├── docs/                  # Documentation
│   ├── API.md             # API reference
│   └── ARCHITECTURE.md    # Architecture overview
├── legacy_data/           # Legacy storage (JSON files, old ChromaDB vectors)
│   ├── storage/           # Chat history, quizzes, flashcards (JSON)
│   └── chroma_db/         # Old ChromaDB vector store
├── sample_data/           # Example JSON curricula and quizzes
├── setup/                 # Platform-specific setup scripts
├── .agents/               # Agent skills (create-skill, repo-reviewer)
│   └── skills/            # Installed agent skills
├── chroma_db/             # Current local vector store (gitignored)
├── docker-compose.yml     # Orchestration (backend + SurrealDB + frontend + unused Postgres)
├── SPEC.md                # Detailed MVP specification
└── REPOSITORY_AUDIT_REPORT.md  # Full multi-agent audit with findings & recommendations
```

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- An [OpenRouter API key](https://openrouter.ai/)

### Setup
```bash
# 1. Clone and configure
cp .env.example .env
# Add your OPENROUTER_API_KEY to .env

# 2. Run the setup script
# Linux/macOS:
bash setup/setup.sh
# Windows:
setup\setup.bat

# 3. Start the backend
cd backend && uvicorn server:app --reload --port 8001

# 4. In another terminal, start the frontend
cd frontend && npm install && npm run dev
```

### Docker (alternative)
```bash
docker compose up --build
```

## Architecture

### Data Flow
```
[PDF Upload] → pdf_extractor.py (text+images) → rag.ingest_pdf()
                                                     ├─ rag.ingest() → ChromaDB.text_chunks
                                                     └─ rag.ingest_images() → ChromaDB.image_chunks

[REST Query] → server.py /query → rag.retrieve() → ChromaDB (both collections)
                                                     └─ query_engine.query() → LLM (OpenRouter)
                                                                                └─ citation validation → response
```

### Services
```
┌──────────┐     ┌──────────┐     ┌───────────┐
│ Frontend │────▶│ Backend  │────▶│ SurrealDB │
│ Next.js  │     │ FastAPI  │     │ (file)    │
│ :3000    │     │ :8001    │     │ :8000     │
└──────────┘     └────┬─────┘     └───────────┘
                       │
                       ▼
                 ┌──────────┐     ┌──────────┐
                 │ OpenRouter│     │ Postgres │
                 │ (LLM +   │     │ (pgvec)  │
                 │ Embed)   │     │ (DEAD)   │
                 └──────────┘     └──────────┘
```

### RAG Pipeline Stages
1. **Gatekeeper** — LLM-based relevance check
2. **Enrichment** — Context assembly
3. **Retrieval** — Hybrid BM25 + vector search with RRF
4. **Generation** — Socratic response via configurable LLM
5. **Verification** — LLM-based grounding check
6. **Citation Enforcement** — Multi-pass citation validation

### Key Design Decisions
- **Two ChromaDB collections**: Separate text (384-dim) and image (1024-dim) embeddings due to Nemotron VL dimension mismatch
- **Magic byte validation**: Only standard image formats (JPEG, PNG, WebP, GIF, TIFF) extracted from PDFs
- **Batch image embedding**: Images grouped in batches of 5 to respect OpenRouter's 26 MB payload limit
- **Lazy OpenRouter singleton**: Client initialized on first use to avoid import-time dependency on `.env`
- **Auth layer exists** (`backend/app/routers/auth.py` with JWT) but is **not enforced** on any route

## Quick Fixes Needed
| Priority | Issue | Location |
|----------|-------|----------|
| 🔴 | Hardcoded API key + JWT secret | `docker-compose.yml:25-26` |
| 🔴 | No auth enforcement on routes | All endpoints |
| 🟠 | Fake token counting (`len(text.split())`) | `chunker.py:6` |
| 🟠 | New HTTPX client per API call (no pooling) | `openrouter.py` (6 locations) |
| 🟠 | `except: pass` swallowing errors | `pdf_extractor.py:95-98` |
| 🟠 | CORS `*` wildcard | `server.py:54-59` |
| 🟠 | No structured logging (all `print()`) | Every backend file |
| 🟠 | No background job system (ingest blocks API) | `server.py` |
| 🟠 | Global module-level singletons with no DI | `server.py:69-73` |
| 🟡 | In-memory SurrealDB in Docker → persistent now fixed | `docker-compose.yml:7` |
| 🟡 | No minimum score threshold in retrieval | `rag.py:164-264` |

For the full audit with 34+ findings, see `REPOSITORY_AUDIT_REPORT.md`.

## MVP Limitations
- Authentication exists (JWT) but is **not enforced** on any route
- No background job system (PDF ingestion blocks API)
- Local ChromaDB (single-user scale)
- Free-tier LLM models (Ring 2.6, Nemotron Nano — limited reasoning)
- No knowledge tracing or spaced repetition
- Postgres service defined but unused (dead infrastructure)
- Two frontends exist with overlapping functionality

## API Overview
See `docs/API.md` for the full API reference. Key endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/ingest` | Upload & ingest PDF |
| `POST` | `/query` | Full RAG query → Socratic response |
| `POST` | `/quiz` | Generate quiz |
| `POST` | `/flashcards` | Generate flashcards |
| `GET` | `/stats` | Course statistics |
| `POST` | `/auth/register` | Register user |
| `POST` | `/auth/login` | Login (returns JWT) |
| `GET` | `/courses` | List courses |
| `POST` | `/generate-paper` | Generate exam paper |

Full specification: `SPEC.md`

## Contributing
See `CONTRIBUTING.md` for guidelines.
