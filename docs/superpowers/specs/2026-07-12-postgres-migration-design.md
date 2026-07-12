# Postgres → SurrealDB Migration & Auth Enforcement

Date: 2026-07-12

## Scope

Migrate all remaining Postgres-backed operations (users, chat history, analytics, saved content) to SurrealDB, enforce auth at middleware level, and fix the embedding dimension mismatch.

## Files to Delete (13)

- `backend/app/models/__init__.py` — re-exports all models + `Base` from `database.py`
- `backend/app/models/user.py` — SQLAlchemy User model
- `backend/app/models/chat.py` — SQLAlchemy ChatMessage model
- `backend/app/models/query_log.py` — SQLAlchemy QueryLog model
- `backend/app/models/flashcard.py` — SQLAlchemy FlashcardSet model
- `backend/app/models/quiz.py` — SQLAlchemy Quiz model
- `backend/app/stores/__init__.py` — re-exports all stores
- `backend/app/stores/user_store.py` — UserStore (SQLAlchemy)
- `backend/app/stores/chat_store.py` — ChatStore (SQLAlchemy)
- `backend/app/stores/analytics_store.py` — AnalyticsStore (SQLAlchemy)
- `backend/app/stores/flashcard_store.py` — FlashcardStore (SQLAlchemy)
- `backend/app/stores/quiz_store.py` — QuizStore (SQLAlchemy)

## SurrealDB Schema (`db.py:_init_schema`)

### Dynamic Dimension Probe

First operation in `_init_schema()` — embed a short test string via `OpenRouterClient.embed_text("probe")`, measure `len(vector)`, and use that value as `$dimension` for all HNSW indexes. If the probe fails (no API key, network error, OpenRouter down), raise a loud startup error. Accept any reasonable dimension (768, 1024, 1536, 2048, 3072).

Reason: the previous code hardcoded `DIMENSION 2048` which silently corrupted search if the model returned a different dimension. Probing at startup guarantees correctness regardless of model changes.

### New Tables

All tables use `SCHEMAFULL` and are added to the existing `_init_schema()` query string.

| Table | Fields |
|---|---|
| `user` | `user_id` (string, UNIQUE), `email` (string, UNIQUE), `hashed_password` (string), `role` (string), `name` (string), `created_at` (datetime DEFAULT `time::now()`) |
| `chat_message` | `user_id` (string), `course_code` (string), `session_id` (string), `message_role` (string), `content` (string), `timestamp` (datetime DEFAULT `time::now()`) |
| `query_log` | `user_id` (string), `course_code` (string), `question` (string), `response_preview` (string), `out_of_scope` (bool), `cited_sources` (array), `timestamp` (datetime DEFAULT `time::now()`) |
| `flashcard_set` | `user_id` (string), `course_code` (string), `topic` (string), `cards` (any), `created_at` (datetime DEFAULT `time::now()`) |
| `quiz` | `user_id` (string), `course_code` (string), `topic` (string), `questions` (any), `score` (int), `total` (int), `created_at` (datetime DEFAULT `time::now()`), `completed_at` (datetime, NULL) |

Indexes on the `user` table: `email` UNIQUE, `user_id` UNIQUE. Indexes on `chat_message`: `course_code + session_id`. All queryable fields get appropriate indexes.

Existing vector tables (`text_chunk`, `image_chunk`, `curriculum_chunk`) use probed `$dimension` instead of hardcoded 2048. `course` and `document` tables unchanged.

### Design Notes

`role` is a reserved concept in SurrealDB's permission system, so `chat_message` uses `message_role` instead. `cited_sources` is a native SurrealDB array rather than a JSON blob — arrays are directly queryable. `cards` and `questions` remain flexible (type `any`) because their structure is expected to evolve. `quiz.completed_at` allows distinguishing finished vs abandoned quizzes for future mastery tracking.

## Rewritten Files (8)

### `app/auth.py`

- Remove `from app.database import Database` and `from app.stores.user_store import UserStore`
- Add `_get_user_by_email(email: str) -> dict | None` — queries SurrealDB `user` table via `SurrealDBManager.get_db()`
- Add `_create_user(email, hashed_password, role)` — `CREATE user CONTENT { ... }` with generated UUID `user_id`
- Public API preserved: `get_user_by_email`, `hash_password`, `verify_password`, `create_access_token`, `decode_token`, `get_current_user`, `require_role` — all unchanged signatures

### `app/chat_history.py`

- Remove `Database` and `ChatStore` imports
- All 3 functions (`get_course_history`, `add_message`, `clear_course_history`) rewritten to use `SurrealDBManager.get_db()`
- Each function gains a `user_id` parameter for user-scoped queries

### `app/analytics.py`

- Remove `Database` and `AnalyticsStore` imports
- All 5 functions (`log_query`, `get_unanswered_questions`, `get_coverage`, `get_analytics`, `get_all_questions`) rewritten to use `SurrealDBManager.get_db()`
- `cited_sources` stored as native SurrealDB array
- Topic analytics still fetched from SurrealDB `text_chunk` table (unchanged)

### `app/saved_content.py`

- Remove `Database`, `FlashcardStore`, `QuizStore` imports
- All 7 methods rewritten to use `SurrealDBManager.get_db()`
- Returned IDs are SurrealDB record IDs (strings) — frontend types already expect strings

### `routers/auth.py`

- Remove `from app.database import Database` and `from app.stores.user_store import UserStore`
- All remaining imports reference `auth.py` functions which are preserved

### `routers/query.py`

- Remove `from app.database import Database`
- Remove the `pg_ok = await Database.health_check()` line from `GET /health`
- Health endpoint checks SurrealDB + OpenRouter only

### `routers/users.py`

- Remove `Database` and `UserStore` imports, remove SQLAlchemy `text()` import
- `GET /users/me` — queries SurrealDB `user` table by email
- `PUT /users/me` — `UPDATE user SET name = $name WHERE email = $email`

### `routers/admin.py`

- Remove `Database` and `UserStore` imports
- `GET /admin/users` — `SELECT * FROM user ORDER BY created_at DESC`
- `GET /admin/stats` — user count via `SELECT count() AS total FROM user GROUP ALL`

## Server Changes (`server.py`)

- Remove `from app.database import Database`
- Remove `Database.init()`, `Database.wait_ready()`, `Database.create_all()` from lifespan startup
- Remove `await Database.close()` from lifespan shutdown
- SurrealDB connection initializes lazily on first `SurrealDBManager.get_db()` call
- `seed_default_users()` rewritten to use `_get_user_by_email()` and `_create_user()` from `auth.py` (SurrealDB-backed)

## Auth Enforcement

- Middleware in `server.py` already validates Bearer token on all non-public prefixes — sufficient for this pass
- Role-level enforcement (`require_role`) deferred to follow-up

## JWT Secret

- Add `backend/.env` to `.gitignore`
- Generate and set a real secret at deploy time

## Verification

1. `docker compose up --build -d` succeeds
2. Backend logs show all 9 routers mounted, no `ImportError`
3. `POST /auth/register` returns `TokenResponse`
4. `POST /auth/login` returns `TokenResponse`
5. `GET /health` returns SurrealDB + OpenRouter status (no Postgres reference)
6. Authenticated request to a protected route succeeds with valid token
7. Authenticated request to a protected route returns 401 with missing/invalid token
