# Architecture (MVP)

## Overview

The platform is a multimodal RAG (Retrieval-Augmented Generation) adaptive learning system. It uses three storage systems (SurrealDB, ChromaDB, JSON files), two frontends, and OpenRouter for all AI/embedding workloads.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTENDS                                   │
│  ┌─────────────────────────┐  ┌──────────────────────────────────┐  │
│  │  frontend/ (production)│  │  new_frontend/ (experimental)    │  │
│  │  Next.js 16, Tailwind   │  │  Next.js 16, plain CSS vars     │  │
│  │  Dockerized (:3000)     │  │  Mock-data based                │  │
│  └─────────────┬───────────┘  └──────────────┬───────────────────┘  │
└────────────────┼──────────────────────────────┼──────────────────────┘
                 │                              │
                 ▼                              ▼
        ┌───────────────────────────────────────────┐
        │           BACKEND (FastAPI :8001)          │
        │                                            │
        │  server.py (entry)                         │
        │  ├── main.py (app factory, lifespan,       │
        │  │   middleware, router includes)          │
        │  ├── app/routers/                          │
        │  │   ├── auth.py        (JWT issue)        │
        │  │   ├── query.py       (health, query,    │
        │  │   │                   query-stream,     │
        │  │   │                   stats, chunks)    │
        │  │   ├── ingestion.py   (ingest,           │
        │  │   │                   curriculum)       │
        │  │   ├── courses.py     (CRUD + curriculum │
        │  │   │                   topics)           │
        │  │   ├── quiz.py        (generate, save,   │
        │  │   │                   list, delete)     │
        │  │   ├── flashcards.py  (generate, save,   │
        │  │   │                   list, delete)     │
        │  │   ├── analytics.py   (analytics,        │
        │  │   │                   unanswered,       │
        │  │   │                   coverage,         │
        │  │   │                   questions)         │
        │  │   ├── chat.py        (get, save,        │
        │  │   │                   clear history)    │
        │  │   └── paper.py       (generate-paper)   │
        │  ├── app/rag.py         (RAG pipeline)     │
        │  ├── app/query_engine.py(Socratic engine)  │
        │  ├── app/openrouter.py  (LLM client)       │
        │  ├── app/db.py          (SurrealDB conn)   │
        │  ├── app/curriculum.py  (curriculum mgmt)  │
        │  ├── app/analytics.py   (analytics logic)  │
        │  ├── app/courses.py     (course CRUD)      │
        │  ├── app/chat_history.py(chat persistence) │
        │  ├── app/saved_content.py(quiz/flashcard   │
        │  │                       persistence)      │
        │  ├── app/paper_generator.py                │
        │  ├── app/chunker.py     (text chunking)    │
        │  ├── app/citation.py    (citation enforce) │
        │  ├── app/gatekeeper.py  (relevance filter) │
        │  ├── app/verifier.py    (grounding check)  │
        │  ├── app/pdf_extractor.py(PDF text+images) │
        │  ├── app/evaluator.py   (RAGAS eval)       │
        │  ├── app/validation.py  (input sanitize)   │
        │  ├── app/auth.py        (JWT helpers)      │
        │  ├── app/config.py      (env config)       │
        │  ├── app/schemas.py     (Pydantic models)  │
        │  └── app/deps.py        (FastAPI DI)       │
        └───────────────┬───────────────────────────┘
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
   ┌──────────┐  ┌──────────┐  ┌────────────┐
   │ SurrealDB│  │ ChromaDB │  │ JSON Files │
   │ (:8000)  │  │ (local)  │  │ (legacy)   │
   │ File-based│  │ text_    │  │ chat_hist, │
   │ persistent│  │ chunks + │  │ quizzes,   │
   │ Docker    │  │ image_   │  │ flashcards │
   │ service   │  │ chunks   │  │            │
   └──────────┘  └──────────┘  └────────────┘
                        │
                        ▼
                  ┌──────────┐
                  │ OpenRouter│
                  │ (external)│
                  │ LLM +     │
                  │ Embeddings│
                  └──────────┘
```

## Storage

### SurrealDB (Primary Database)
- **Type**: Document database with HNSW vector index support
- **Mode**: Persistent file mode in Docker (`file://data/surrealdb.db`)
- **Tables**: `course`, `text_chunk`, `image_chunk`, `curriculum_chunk`, `chat_history`, `flashcard_set`, `quiz`, `query_log`, `users`
- **Schema**: Recreated on startup via `_init_schema()` — no migration system
- **Access**: Direct SurrealQL queries (no ORM/abstraction layer)

### ChromaDB (Vector Store)
- **Two collections**: `text_chunks` (384-dim) and `image_chunks` (1024-dim)
- **Location**: `./chroma_db/` (gitignored)
- **Usage**: Hybrid BM25 + vector similarity search with RRF fusion

### JSON Files (Legacy)
- Course data, chat history, saved quizzes/flashcards stored in `./legacy_data/`
- Being migrated to SurrealDB

## AI Pipeline

### Models
| Use | Provider | Model |
|-----|----------|-------|
| Text embeddings | OpenRouter (free) | `nvidia/llama-nemotron-embed-vl-1b-v2:free` |
| Image embeddings | OpenRouter (free) | Same (multimodal mode, 1024-dim) |
| LLM (reasoning) | OpenRouter (free) | `inclusionai/ring-2.6-1t:free` |

### RAG Pipeline Stages
1. **Gatekeeper** — LLM checks if query is course-relevant
2. **Enrichment** — Assembles context from retrieved chunks
3. **Retrieval** — Hybrid BM25 + vector search, RRF fusion
4. **Generation** — Socratic response via Ring LLM
5. **Verification** — LLM verifies answer is grounded in context
6. **Citation Enforcement** — Multi-pass citation validation

### Performance
- Single query: ~2-5s (3 LLM calls: gatekeeper, strategy, answer)
- PDF ingestion (15MB): ~20-40s (blocking, no background job)
- Batch embedding: single-batch, no parallelism

## Services (Docker Compose)

| Service | Status | Notes |
|---------|--------|-------|
| `surrealdb` | ✅ Active | Persistent file mode, port 8000 |
| `backend` | ✅ Active | FastAPI, port 8001 |
| `frontend` | ✅ Active | Next.js 16, port 3000 |
| `postgres` | ❌ Dead | Defined but no code connects to it |

## Auth

An auth layer exists (`backend/app/routers/auth.py` and `backend/app/auth.py`) with JWT token issuance. However:
- No route has `Depends(get_current_user)` or token validation middleware
- Auth endpoints (`/auth/register`, `/auth/login`) work but tokens are never enforced
- CORS is now configurable via `CORS_ORIGINS` env var (not wildcard `*`)

## Two Frontends

| Aspect | `frontend/` | `new_frontend/` |
|--------|------------|-----------------|
| Purpose | Production Dockerized UI | Experimental prototype |
| Styling | Tailwind CSS v4 | Plain CSS custom properties |
| Language | TypeScript | JavaScript |
| Data source | Real API calls | Mock data (`src/lib/mockData.js`) |
| Dockerized | Yes (Dockerfile in repo) | No |

## Key Technical Debt
- No DI/IoC — global singletons at module level
- No background job system — `POST /ingest` blocks the API server
- Fake token counting (`len(text.split())`) — all chunk boundaries wrong
- New HTTPX client per API call — no connection pooling
- `print()` statements instead of structured logging
- `except: pass` silently swallows errors in PDF extraction
- Single file server.py (568 lines) — all routes, models, and lifespan in one module
- No database abstraction layer — direct SurrealQL in every module
- SurrealDB connection manager has deadlock risk on failed connection
- Postgres service defined but unused
