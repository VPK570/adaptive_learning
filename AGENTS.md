# Adaptive Learning Platform — Agent Guide

## Project State (MVP, ~3/10 readiness)

- **Single frontend:** `new_frontend/` (JS + CSS, `strict: false`).
- **Backend/.env** uses placeholder JWT secret. Set a real one before deploying.

## Backend

- **FastAPI entry:** `backend/server.py` — mounts 9 routers (query, courses, analytics, chat, ingestion, flashcards, quiz, paper, auth).
- **SurrealDB** is the real DB. Postgres service was removed from docker-compose (nothing uses it).
- **Auth exists but is dead code:** `auth.py` has JWT + bcrypt, login/register endpoints work, but **no route uses `Depends(get_current_user)`**. Frontend stores tokens in localStorage but never sends them.
- **Schema dimension gotcha:** SurrealDB HNSW indexes are hardcoded to `DIMENSION 2048` in `db.py`. README says 384 (text) / 1024 (image) — ignore README, the code is right.

## Frontend (new_frontend)

- **All pages use mock data** (`src/lib/mockData.ts`) except the login page. Backend has working endpoints for quiz, flashcards, chat-history, courses, analytics, generate-paper, ingest — none are wired up.
- **API client** (`src/lib/api.js`) only handles login/register. Needs extension to cover all endpoints with Bearer token support.
- **CSS:** Custom properties in `globals.css` + per-page CSS modules (`page.module.css`). No Tailwind.

## Commands

```bash
# Backend
cd backend && uvicorn server:app --reload --port 8001
cd backend && pytest tests/ -v           # 4 test files, SurrealDB fixtures
cd backend && ruff check .               # no config file — uses defaults

# Frontend (new_frontend)
cd new_frontend && npm run dev           # dev server on :3000
cd new_frontend && npm run build         # will FAIL (ignoreBuildErrors:true)
cd new_frontend && npm run lint          # no ESLint config — no-op

# Docker
docker compose up -d                     # starts surrealdb + backend + frontend
```

## Key Gotchas

- **No CI/CD** — no GitHub workflows, no pre-commit hooks.
- **No formatter config** — no `.prettierrc`, `.editorconfig`, `.ruff.toml`. Only Ruff in requirements.txt with no config.
- **`SPEC.md` is superseded** — it's been replaced with a stub; see `docs/API.md` for API docs.

## Developer Conventions

- Prefer reading `docs/API.md` (407 lines) for backend endpoint reference — it's the most up-to-date API doc.
- Backend pattern: module-level async, Pydantic validated schemas in `schemas.py`, DI via `deps.py` pulling from `app.state`.
