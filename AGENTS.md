# Adaptive Learning Platform — Agent Guide

## Project State (MVP, ~3/10 readiness)

- **Single frontend:** `new_frontend/` (Next.js 16, JS + CSS, `strict: false`).
- **Backend/.env** uses placeholder JWT secret (`change_this_to_a_random_secret`). Set a real one before deploying.
- **5 Docker services:** surrealdb, backend, redis, worker (Celery), frontend.

## Architecture & Entrypoints

- **Backend:** `backend/server.py` — FastAPI, mounts 14 routers (auth, query, courses, chat, ingestion, flashcards, quiz, paper, analytics, images, admin, users, learning_path, tasks).
- **Frontend:** `new_frontend/` — Next.js 16 App Router. Login at `/`; role dashboards at `/student/*`, `/faculty/*`, `/admin/*`.
- **DB:** SurrealDB only (no Postgres). Schema (`db.py:_init_schema`) recreated on startup — no migration system. HNSW dimension probed dynamically.
- **LLM routing:** Chat → Gemini (multi-key), Embeddings → OpenRouter (NVIDIA Nemotron). KeyRing rotates keys with exponential backoff on 429.

## Backend

- **Auth:** Middleware in `server.py` validates JWT on every non-public request, sets `request.state.user`. Role checks via `require_role()` from `app/auth.py`. Public routes: `/auth`, `/health`, `/docs`, `/openapi.json`, `/redoc`, `GET /chat-images/*`.
- **Default users** (created on startup): `student@test.com`, `faculty@test.com`, `admin@test.com` — all password `password123`.
- **DI:** `app/deps.py` pulls services from `app.state` (RAGPipeline, QueryEngine, CurriculumManager, KnowledgeStateManager). No IoC container.
- **RAG pipeline:** Gatekeeper → Enrichment → Hybrid Retrieval (BM25+vector HNSW, RRF) → Generation → Verification → Citation.
- **Celery worker** at `app/tasks.py` for background ingestion. Requires Redis. Composed as `worker` service.

## Frontend (new_frontend)

- **API proxy:** Next.js rewrites in `next.config.mjs` — not direct CORS. All backend routes are proxied.
- **API client:** `src/lib/api/client.ts` — axios instance auto-attaches Bearer token from zustand auth store, logs out on 401.
- **Auth store:** zustand with localStorage persistence (key: `uniauth`). Login sends `application/x-www-form-urlencoded` (OAuth2PasswordRequestForm).
- **CSS:** Custom properties in `globals.css` + per-page CSS modules (`page.module.css`). No Tailwind.

## Commands

```bash
# Backend
cd backend && uvicorn server:app --reload --port 8001    # dev server
cd backend && pytest tests/ -v                            # 10 tests, needs running SurrealDB
cd backend && pytest tests/test_auth.py -v                # pure unit tests (no DB)
cd backend && ruff check .                                # config: ruff.toml (line-length=120, py311)

# Frontend
cd new_frontend && npm run dev          # :3000
cd new_frontend && npm run build        # ignoreBuildErrors:true, may succeed with TS errors
cd new_frontend && npm run lint         # functional — eslint.config.mjs (next/core-web-vitals)

# Docker (all 5 services)
docker compose up -d

# Just infra (for local backend dev)
docker compose up -d surrealdb redis
```

## Gotchas

- **No CI/CD** — no GitHub workflows, no pre-commit hooks.
- **No formatter config** — no `.prettierrc`, no `.editorconfig`.
- **`SPEC.md` deleted** — see `docs/API.md` for API ref, `docs/ARCHITECTURE.md` for system design.
- **`.env.example` has dead `CHROMA_PATH`** — ChromaDB removed. SurrealDB settings only in `backend/.env`.
- **Backend tests** need running SurrealDB. `conftest.py` overrides to `test_ns`/`test_db` and cleans all tables between tests.
- **Frontend build ignores TS errors** (`tsconfig.json: strict: false`, `next.config.mjs: ignoreBuildErrors: true`).
- **Login format:** frontend sends `application/x-www-form-urlencoded` to `/auth/login`, not JSON. Backend uses `OAuth2PasswordRequestForm`.
- **Docker backend** expects SurrealDB at `ws://surrealdb:8000/rpc` and Redis at `redis:6379` (compose env vars).
- **`new_frontend/CLAUDE.md`** just contains `@AGENTS.md` (include directive); `new_frontend/AGENTS.md` has a Next.js 16 breaking-changes warning — heed it.

## Knowledge Graph

**Always use graphify** to answer questions, edit code, or review changes. Before touching any file, run `graphify query "<question>"` against `graphify-out/graph.json` to understand relationships, dependencies, and affected modules. This avoids breaking cross-community connections.

- `graph.html` — interactive visualization (open in browser)
- `GRAPH_REPORT.md` — audit report with god nodes, surprising connections, community labels
- `graph.json` — raw graph data for programmatic access
- Rebuild with `/graphify` after significant code changes
