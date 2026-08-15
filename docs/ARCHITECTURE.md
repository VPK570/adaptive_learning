# Architecture (MVP)

## Overview

The platform is a multimodal RAG (Retrieval-Augmented Generation) adaptive learning system. It uses SurrealDB as the primary database, and a provider router for AI workloads (Gemini for chat, OpenRouter for embeddings).

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTENDS                                   │
│  ┌─────────────────────────┐  ┌──────────────────────────────────┐  │
│  │  new_frontend/            │  │
│  │  Next.js 16, plain CSS   │  │
│  │  Dockerized (:3000)      │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
                 │
                 ▼
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
         │  │   ├── quiz.py        (generate)          │
         │  │   ├── flashcards.py  (generate)          │
        │  │   ├── analytics.py   (analytics,        │
        │  │   │                   unanswered,       │
        │  │   │                   coverage,         │
        │  │   │                   questions)         │
         │  │   ├── chat.py        (history CRUD)      │
         │  │   ├── paper.py       (generate-paper)   │
         │  │   ├── users.py       (profile)           │
         │  │   ├── admin.py       (stats + users)     │
         │  │   ├── learning_path.py (recommendations)│
         │  │   └── tasks.py       (Celery tasks)      │
        │  ├── app/rag.py         (RAG pipeline)     │
        │  ├── app/query_engine.py(Socratic engine)  │
        │  ├── app/provider_router.py (LLM routing)  │
        │  ├── app/db.py          (SurrealDB conn)   │
        │  ├── app/curriculum.py  (curriculum mgmt)  │
        │  ├── app/analytics.py   (analytics logic)  │
        │  ├── app/courses.py     (course CRUD)      │
        │  ├── app/chat_history.py(chat persistence) │
        │  ├── app/topics.py      (topic analysis)   │
         │  ├── app/learning_path.py(ZPD recs)         │
        │  ├── app/paper_generator.py                │
        │  ├── app/chunker.py     (text chunking)    │
        │  ├── app/citation.py    (citation enforce) │
        │  ├── app/gatekeeper.py  (relevance filter) │
        │  ├── app/verifier.py    (grounding check)  │
        │  ├── app/pdf_extractor.py(PDF text+images) │
        │  ├── app/evaluator.py   (RAGAS eval)        │
        │  ├── app/validation.py  (input sanitize)   │
        │  ├── app/auth.py        (JWT helpers)      │
        │  ├── app/config.py      (env config)       │
        │  ├── app/schemas.py     (Pydantic models)  │
        │  └── app/deps.py        (FastAPI DI)       │
        └───────────────┬───────────────────────────┘
                        │
                      ▼
               ┌──────────┐
               │ SurrealDB│
               │ (:8000)  │
               │ File-based│
               │ persistent│
               │ Docker   │
               │ service  │
                └──────────┘
                         │
                         ▼
                   ┌──────────┐
                   │Provider  │
                   │Router    │
                   │(Gemini + │
                   │OpenRouter)│
                   └──────────┘
```

## Storage

### SurrealDB (Primary Database)
- **Type**: Document database with HNSW vector index support
- **Mode**: Persistent file mode in Docker (`file://data/surrealdb.db`)
- **Tables**: `course`, `text_chunk`, `image_chunk`, `curriculum_chunk`, `chat_history`, `flashcard_set`, `quiz`, `query_log`, `users`
- **Schema**: Recreated on startup via `_init_schema()` — no migration system
- **Access**: Direct SurrealQL queries (no ORM/abstraction layer)

### Vector Search
- Hybrid BM25 + vector similarity search with RRF fusion (all in SurrealDB)
- HNSW indexes on `text_chunk.embedding`, `image_chunk.embedding`, `curriculum_chunk.embedding`
- Dimension probed dynamically at startup via provider_router embedding call

## AI Pipeline

### Models
| Use | Provider | Model |
|-----|----------|-------|
| Text embeddings | OpenRouter (free) | `nvidia/llama-nemotron-embed-vl-1b-v2:free` |
| Image embeddings | OpenRouter (free) | Same (multimodal mode, 1024-dim) |
| LLM (reasoning) | Gemini (via provider_router) | Multi-key rotation with exponential backoff |

### RAG Pipeline Stages
1. **Gatekeeper** — LLM checks if query is course-relevant
2. **Enrichment** — Assembles context from retrieved chunks
3. **Retrieval** — Hybrid BM25 + vector search, RRF fusion with late chunking
4. **Generation** — Socratic response via Gemini
5. **Verification** — LLM verifies answer is grounded in context
6. **Citation Enforcement** — Multi-pass citation validation

### Performance
- Single query: ~2-5s (3 LLM calls: gatekeeper, strategy, answer)
- PDF ingestion (15MB): ~20-40s (blocked by Celery task or inline)
- Batch embedding: single-batch, no parallelism

## Services (Docker Compose)

| Service | Status | Notes |
|---------|--------|-------|
| `surrealdb` | ✅ Active | Persistent file mode, port 8000 |
| `backend` | ✅ Active | FastAPI, port 8001 |
| `frontend` | ✅ Active | Next.js 16, port 3000 |
| `redis` | ✅ Active | Celery broker |
| `worker` | ✅ Active | Celery worker for background tasks |

## Auth

Auth is enforced via a middleware in `server.py` that validates Bearer JWT tokens on all routes except `/auth`, `/health`, `/healthz`, `/docs`, `/tasks`. Role-based access control is available via `require_role()` decorator from `app/auth.py` (used by admin, ingestion, and paper routers).

## Key Technical Debt
- No DI/IoC — global singletons at module level  
- Fake token counting (`len(text.split())`) — all chunk boundaries approximate
- `print()` statements instead of structured logging
- `except: pass` silently swallows errors in PDF extraction
- No database abstraction layer — direct SurrealQL in every module
- SurrealDB connection manager has deadlock risk on failed connection
- Deleted `deep_kt.py` and `openrouter.py` — functionality moved to provider_router.py
