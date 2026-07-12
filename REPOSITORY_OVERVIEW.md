# Adaptive Learning Platform — Complete Codebase Reference

> **Purpose:** Provide comprehensive context for another AI agent to understand, navigate, and modify this codebase.
> **Generated:** 2026-07-12 | **Commit:** `363b183` | **Branch:** `main`

---

## Table of Contents
1. [Stack Overview](#1-stack-overview)
2. [Directory Map](#2-directory-map)
3. [Backend: Entrypoint & Configuration](#3-backend-entrypoint--configuration)
4. [Backend: Core Modules](#4-backend-core-modules)
5. [Backend: Routers (API Layer)](#5-backend-routers-api-layer)
6. [Backend: Database Layer](#6-backend-database-layer)
7. [Backend: Auth Layer](#7-backend-auth-layer)
8. [Backend: Tests](#8-backend-tests)
9. [Frontend: Production (`frontend/`)](#9-frontend-production-frontend)
10. [Frontend: Experimental (`new_frontend/`)](#10-frontend-experimental-new_frontend)
11. [Infrastructure & Docker](#11-infrastructure--docker)
12. [Documentation](#12-documentation)
13. [Dead Code Inventory](#13-dead-code-inventory)
14. [Data Flow: Complete Traces](#14-data-flow-complete-traces)
15. [Known Gotchas & Pitfalls](#15-known-gotchas--pitfalls)

---

## 1. Stack Overview

| Layer | Technology | Version | Port | Notes |
|-------|-----------|---------|------|-------|
| **Backend framework** | FastAPI (Python) | 0.115.0 | 8001 | ASGI, auto OpenAPI docs at `/docs` |
| **Primary database** | SurrealDB | latest (Docker) | 8000 | Persistent file mode, document + vector store |
| **Vector search** | SurrealDB HNSW | — | — | DIMENSION 2048, COSINE distance |
| **LLM provider** | OpenRouter | — | — | Free tier: Nemotron VL embed + Nemotron Nano chat |
| **Production frontend** | Next.js 16 | 16.2.6 | 3000 | TypeScript 5, `strict: true`, Tailwind v4, Docker `standalone` |
| **Experimental frontend** | Next.js 16 | 16.2.9 | 3000 | TS + JS, `strict: false`, `ignoreBuildErrors: true`, pure CSS dark theme |
| **Auth** | JWT (python-jose) + bcrypt (passlib) | — | — | Self-hosted, **not enforced** |
| **Containerization** | Docker Compose | 3.9 | — | 4 services defined, 1 dead (Postgres) |
| **Dead service** | Postgres (pgvector) | pg16 | 5433 | No code connects to it |

---

## 2. Directory Map

```
/
├── backend/                          # 🎯 FastAPI backend — 4364 lines Python
│   ├── server.py                     # Entrypoint: creates FastAPI app, mounts 9 routers, CORS, rate limiting, lifespan
│   ├── Dockerfile                    # python:3.11-slim → pip install → uvicorn
│   ├── requirements.txt              # 24 deps (chromadb, surrealdb, httpx, fastapi, jose, bcrypt, etc.)
│   ├── .env                          # ⚠️ COMMITTED — contains real JWT secret
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py                 # Settings class — reads from env vars, lru_cache singleton
│   │   ├── db.py                     # SurrealDBManager — singleton connection pool, schema init, health check
│   │   ├── database.py               # 💀 DEAD — SQLAlchemy async Postgres engine + session factory
│   │   ├── deps.py                   # FastAPI Depends() helpers — get_rag, get_engine, get_curriculum, get_saved_content
│   │   ├── schemas.py                # Pydantic models — QueryRequest, PaperRequest, CourseCreate/Update, Flashcard/Quiz requests
│   │   ├── validation.py             # Input sanitization, injection detection, size limits, regex patterns
│   │   ├── rag.py                    # RAGPipeline — ingest, ingest_images, ingest_pdf, retrieve (hybrid search), stats
│   │   ├── query_engine.py           # QueryEngine — builds prompts, streams responses, citation enforcement
│   │   ├── openrouter.py             # OpenRouterClient — embed_text, embed_images, chat, stream, chat_with_schema
│   │   ├── chunker.py                # Text chunker — 512-token sentence-aware, tiktoken-based
│   │   ├── pdf_extractor.py          # PDF parser — pypdf text + image extraction, magic byte validation
│   │   ├── curriculum.py             # CurriculumManager — ingest, list, topics extraction, relevance check
│   │   ├── courses.py                # Course CRUD — get_all, create, update, delete (SurrealDB)
│   │   ├── chat_history.py           # Chat history — get, add, clear (uses dead Postgres path)
│   │   ├── analytics.py              # Analytics — log_query, get_analytics, coverage, unanswered (uses dead Postgres)
│   │   ├── saved_content.py          # Saved flashcards/quizzes CRUD (uses dead Postgres)
│   │   ├── auth.py                   # JWT create/decode, password hash/verify, get_current_user, require_role
│   │   ├── citation.py               # Citation extraction, parsing, validation, removal of uncited claims
│   │   ├── gatekeeper.py             # LLM-based relevance gatekeeper — checks if query is on-topic
│   │   ├── verifier.py               # LLM-based verification — checks if answer is grounded in sources
│   │   ├── paper_generator.py        # Exam paper generator — configurable marks, difficulty, Bloom's taxonomy
│   │   ├── evaluator.py              # RAGAS-style eval — faithfulness, relevancy, precision, recall
│   │   ├── models/                   # 💀 DEAD — SQLAlchemy ORM models (5 files, ~84 lines total)
│   │   │   ├── user.py               # User — id, email, hashed_password, role, created_at
│   │   │   ├── chat.py               # ChatMessage — id, course_code, session_id, role, content, timestamp
│   │   │   ├── flashcard.py          # FlashcardSet — id, course_code, topic, cards (JSON), created_at
│   │   │   ├── quiz.py               # Quiz — id, course_code, topic, questions (JSON), score, total, created_at
│   │   │   └── query_log.py          # QueryLog — id, course_code, question, response_preview, timestamp, out_of_scope, cited_sources
│   │   ├── stores/                   # 💀 DEAD — SQLAlchemy async CRUD stores (5 files, ~200 lines)
│   │   │   ├── user_store.py         # User CRUD — get_by_email, create
│   │   │   ├── chat_store.py         # Chat CRUD — get_history, add_message, clear_history
│   │   │   ├── flashcard_store.py    # Flashcard CRUD — save, get_all, delete
│   │   │   ├── quiz_store.py         # Quiz CRUD — save, get_all, delete
│   │   │   └── analytics_store.py    # Analytics CRUD — log_query, get_unanswered, get_all_for_course, get_coverage
│   │   └── routers/                  # API route handlers (9 files)
│   │       ├── __init__.py
│   │       ├── query.py              # Routes: /health, /stats, /chunks, /query, /query-stream
│   │       ├── auth.py               # Routes: /auth/register, /auth/login
│   │       ├── ingestion.py          # Routes: /ingest, /curriculum (upload)
│   │       ├── quiz.py               # Routes: /quiz, /quiz/save, /quiz/saved, /quiz/saved/{id}
│   │       ├── flashcards.py         # Routes: /flashcards, /flashcards/save, /flashcards/saved, /flashcards/saved/{id}
│   │       ├── courses.py            # Routes: /courses CRUD, /curriculum/topics, /curriculum (list)
│   │       ├── analytics.py          # Routes: /analytics, /analytics/unanswered, /analytics/coverage, /questions
│   │       ├── chat.py               # Routes: /chat-history (get, add, delete)
│   │       └── paper.py              # Route: /generate-paper
│   ├── tests/                        # 4 test files, ~500 lines
│   │   ├── conftest.py               # SurrealDB fixtures — creates test connection, cleanup after each test
│   │   ├── test_rag.py               # Chunking, citation parsing, prompt building, RAG pipeline integration tests
│   │   ├── test_validation.py        # ID sanitization/validation unit tests
│   │   ├── test_api_limits.py        # Upload size middleware integration tests
│   │   └── test_db_logic.py          # SurrealDB CRUD, curriculum, chat, analytics tests
│   └── storage/                      # Runtime data — JSON files for legacy storage
│
├── frontend/                         # 🎯 Production Next.js frontend — fully API-wired
│   ├── app/
│   │   ├── page.tsx                  # Student dashboard — fetches /courses, /questions, shows progress rings
│   │   ├── layout.tsx                # Root layout with Navbar, Inter font
│   │   ├── globals.css               # Tailwind v4 import + 2 CSS vars (light theme)
│   │   ├── chat/page.tsx             # AI Tutor — SSE streaming via /query-stream, sessions
│   │   ├── progress/page.tsx         # Learning progress — weak areas, revision, daily activity
│   │   ├── quiz/page.tsx             # Quiz — generate, take, save, review, delete
│   │   ├── flashcards/page.tsx       # Flashcards — generate, flip, navigate, save, load, delete
│   │   └── faculty/
│   │       ├── page.tsx              # Faculty course management — CRUD
│   │       ├── generate/page.tsx     # Exam paper generator
│   │       ├── analytics/page.tsx    # Top questions, weak topics tag cloud, charts
│   │       └── course/[code]/page.tsx # 4-tab detail: Materials, Analytics, Unanswered, Coverage
│   ├── lib/api.ts                    # API client — fetch wrapper, JSON only, no Bearer token
│   ├── Dockerfile                    # Multi-stage build with standalone output
│   ├── next.config.ts                # strict: true (TypeScript), no ignoreBuildErrors
│   ├── tsconfig.json                 # strict: true, moduleResolution: bundler
│   └── package.json                  # Next.js 16.2.6, React 19.2.4, TypeScript 5.x, Tailwind v4
│
├── new_frontend/                     # 🧪 Experimental Next.js frontend — 13/14 pages use mock data
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx              # Login page — only page wired to real API
│   │   │   ├── layout.tsx            # Root layout — Inter + JetBrains Mono fonts
│   │   │   ├── globals.css           # Full dark design system: 100+ CSS vars, component classes
│   │   │   ├── student/
│   │   │   │   ├── dashboard/page.tsx        # Student dashboard — radial mastery, streak, course grid
│   │   │   │   ├── quiz/page.tsx             # "Under development" placeholder
│   │   │   │   ├── progress/page.tsx         # Stats tiles, topic breakdowns, heatmap, revision
│   │   │   │   ├── profile/page.tsx          # Bare placeholder
│   │   │   │   ├── flashcards/page.tsx       # "Under development" placeholder
│   │   │   │   ├── courses/[code]/page.tsx   # Course detail with chat panel (mock messages)
│   │   │   │   └── chat/page.tsx             # "Coming soon" placeholder
│   │   │   ├── faculty/
│   │   │   │   ├── dashboard/page.tsx        # Faculty overview — stats, activity, course grid
│   │   │   │   ├── generate/page.tsx         # Paper configurator with Bloom levels
│   │   │   │   ├── profile/page.tsx          # Bare placeholder
│   │   │   │   ├── course/[code]/page.tsx    # Upload materials with dropzone + file list
│   │   │   │   └── analytics/page.tsx        # "Coming soon" placeholder
│   │   │   ├── admin/
│   │   │   │   ├── dashboard/page.tsx        # Admin stats, activity chart, sign-ups, user table
│   │   │   │   └── profile/page.tsx          # Bare placeholder
│   │   │   └── components/           # 20 reusable UI components
│   │   │       ├── AppShell.tsx       # Main layout wrapper with sidebar
│   │   │       ├── Sidebar.tsx        # Navigation sidebar
│   │   │       ├── TopBar.tsx         # Top navigation bar
│   │   │       ├── CourseCard.tsx     # Course display card
│   │   │       ├── StatTile.tsx       # Metric display tile
│   │   │       ├── RadialProgress.tsx # Circular progress indicator
│   │   │       ├── ProgressBar.tsx    # Linear progress bar
│   │   │       ├── ActivityHeatmap.tsx # GitHub-style activity heatmap
│   │   │       ├── MiniBarChart.tsx   # Small bar chart
│   │   │       ├── DataTable.tsx      # Data table with rows/columns
│   │   │       ├── Badge.tsx          # Status badge
│   │   │       ├── BloomPill.tsx      # Bloom's taxonomy level pill
│   │   │       ├── Breadcrumbs.tsx    # Breadcrumb navigation
│   │   │       ├── AvatarOrInitials.tsx # User avatar/initials
│   │   │       ├── Dropzone.tsx       # File upload dropzone
│   │   │       ├── FileTypeIcon.tsx   # File type icon
│   │   │       ├── FormField.tsx      # Form input field
│   │   │       ├── CheckboxCard.tsx   # Checkbox card
│   │   │       ├── RemovableSection.tsx # Section with remove button
│   │   │       └── PaperPreview.tsx   # Generated paper preview
│   │   └── lib/
│   │       ├── api.js                 # API client — only login/register (30 lines, no Bearer)
│   │       └── mockData.ts            # 24 mock exports — all data for 13 pages
│   ├── next.config.mjs                # ignoreBuildErrors: true
│   ├── tsconfig.json                  # strict: false
│   ├── eslint.config.mjs
│   ├── jsconfig.json
│   └── package.json                   # Next.js 16.2.9, React 19.2.4, TypeScript 6.0.3
│
├── docs/
│   ├── API.md                         # 407-line API reference (most up-to-date)
│   ├── ARCHITECTURE.md                # 164-line architecture overview
│   ├── ARCHITECTURE_CONNECTIONS.md    # Connection diagrams
│   ├── FRONTEND_BACKEND_INTEGRATION.md
│   ├── RAG_VS_OPENNOTEBOOK.md         # Comparison with Open Notebook
│   ├── SETUP.md                       # Setup guide (references non-existent setup/migrate.sh)
│   └── diagrams/                      # Excalidraw architecture diagrams
│       └── all-diagrams.excalidraw
│
├── docker-compose.yml                 # 4 services: surrealdb, backend, frontend, postgres (dead)
├── .env.example                       # Env template — OPENROUTER_API_KEY, JWT_SECRET, etc.
├── .gitignore                         # Ignores .env, node_modules, __pycache__, chroma_db/, etc.
├── AGENTS.md                          # Agent guide — project state, gotchas, commands
├── CONTRIBUTING.md                    # Contribution guide
├── SPEC.md                            # MVP spec (partially outdated)
├── REPOSITORY_AUDIT_REPORT.md         # Full security/code audit
├── README.md                          # Project README with feature list, quick start, known issues
│
├── setup/                             # Setup scripts — ALL 3 ARE BROKEN
│   ├── setup.sh                       # Wrong cp path + wrong sed placeholder
│   ├── setup.bat                      # Same bugs as .sh
│   └── setup.ps1                      # Same bugs as .sh
│
├── scripts/
│   └── generate_excalidraw.py         # 828-line utility → generates 10 Excalidraw diagrams
│
├── sample_data/                       # Example JSON curricula/quizzes
├── legacy_data/                       # Old JSON storage + old ChromaDB vectors
├── chroma_db/                         # Unused ChromaDB directory (SurrealDB replaced it)
├── .worktrees/                        # Git worktrees for parallel development
├── opencode.json                      # Opencode agent config
└── skills-lock.json                   # Agent skills lockfile
```

---

## 3. Backend: Entrypoint & Configuration

### 3.1 `backend/server.py` (81 lines)

This is the **application entrypoint**. It does:

**A. Imports and setup (lines 1-24):**
```python
# Loads .env, adds app/ to sys.path
load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))
# Imports 7 module classes + 9 routers
```
`sys.path.insert` is needed because `server.py` lives in `backend/`, but imports reference `app.config`, `app.rag`, etc.

**B. Lifespan handler (lines 33-41):**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.rag = RAGPipeline()           # Global RAG singleton
    app.state.engine = QueryEngine()         # Global QueryEngine singleton
    app.state.curriculum = CurriculumManager()  # Global Curriculum singleton
    app.state.saved_content = SavedContentManager()  # Global SavedContent singleton
    yield
```
Four singletons initialized at startup and stored in `app.state`. They're accessed via `deps.py` DI helpers.

**C. Middleware stack (lines 44-66):**
- **Rate limiting** via `slowapi`: 60 req/min per IP, in-memory (resets on restart)
- **CORS**: Configured from `settings.CORS_ORIGINS` env var (default `http://localhost:3000`)
- **Upload size limit**: Custom middleware checks `content-length` header on POST/PUT, rejects >15MB with 413

**D. Router mounting (lines 69-77):**
```python
app.include_router(query.router)       # /health, /stats, /chunks, /query, /query-stream
app.include_router(courses.router)     # /courses CRUD, /curriculum GET endpoints
app.include_router(analytics.router)   # /analytics, /unanswered, /coverage, /questions
app.include_router(chat.router)        # /chat-history CRUD
app.include_router(ingestion.router)   # /ingest, /curriculum POST
app.include_router(flashcards.router)  # /flashcards CRUD
app.include_router(quiz.router)        # /quiz CRUD
app.include_router(paper.router)       # /generate-paper
app.include_router(auth_routes.router) # /auth/register, /auth/login
```

**E. Direct execution (lines 79-81):**
```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

### 3.2 `backend/app/config.py` (56 lines)

Settings are read from environment variables at import time via a `Settings` class with a `@lru_cache` singleton:

```python
@lru_cache
def get_settings() -> "Settings":
    return Settings()
```

Key settings with their env var names and defaults:

| Setting | Env Var | Default | Notes |
|---------|---------|---------|-------|
| `CORS_ORIGINS` | `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated |
| `SURREAL_URL` | `SURREAL_URL` | `ws://localhost:8000/rpc` | WebSocket protocol |
| `SURREAL_NS` | `SURREAL_NS` | `adaptive_learning` | |
| `SURREAL_DB` | `SURREAL_DB` | `learning_platform` | |
| `SURREAL_USER` | `SURREAL_USER` | `root` | |
| `SURREAL_PASS` | `SURREAL_PASS` | `root` | |
| `OPENROUTER_API_KEY` | `OPENROUTER_API_KEY` | `""` | Warns if empty or placeholder |
| `OPENROUTER_BASE_URL` | `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | |
| `EMBEDDING_MODEL` | `EMBEDDING_MODEL` | `nvidia/llama-nemotron-embed-vl-1b-v2:free` | |
| `LLM_MODEL` | `LLM_MODEL` | `nvidia/nemotron-3-nano-30b-a3b:free` | |
| `RAG_TOP_K` | `RAG_TOP_K` | `5` | |
| `CHUNK_SIZE` | `CHUNK_SIZE` | `512` | Token count |
| `CHUNK_OVERLAP_TOKENS` | `CHUNK_OVERLAP_TOKENS` | `64` | |
| `IMAGE_MAX_BATCH_SIZE` | `IMAGE_MAX_BATCH_SIZE` | `5` | |
| `IMAGE_MAX_PER_PDF` | `IMAGE_MAX_PER_PDF` | `50` | |
| `RRF_K` | `RRF_K` | `60` | RRF constant |
| `HNSW_EF_SEARCH` | `HNSW_EF_SEARCH` | `40` | |
| `MAX_HISTORY_TURNS` | `MAX_HISTORY_TURNS` | `8` | |
| `JWT_SECRET` | `JWT_SECRET` | `""` | Warns if empty |
| `JWT_ALGORITHM` | `JWT_ALGORITHM` | `HS256` | |
| `JWT_EXPIRE_MINUTES` | `JWT_EXPIRE_MINUTES` | `1440` | 24 hours |
| `CURRICULUM_K` | `CURRICULUM_K` | `3` | |
| `CURRICULUM_EF` | `CURRICULUM_EF` | `40` | |
| `CURRICULUM_THRESHOLD` | `CURRICULUM_THRESHOLD` | `0.6` | |
| `RAG_MIN_SIMILARITY` | `RAG_MIN_SIMILARITY` | `0.4` | |
| `DATABASE_URL` | `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5433/adaptive_learning` | 💀 Dead |
| `DB_ECHO_SQL` | `DB_ECHO_SQL` | `false` | 💀 Dead |
| `DB_POOL_SIZE` | `DB_POOL_SIZE` | `10` | 💀 Dead |
| `DB_MAX_OVERFLOW` | `DB_MAX_OVERFLOW` | `20` | 💀 Dead |

Constructor warnings:
```python
def __init__(self):
    if not self.JWT_SECRET or self.JWT_SECRET == "":
        logger.warning("JWT_SECRET is not set")
    if not self.OPENROUTER_API_KEY or "your_" in self.OPENROUTER_API_KEY:
        logger.warning("OPENROUTER_API_KEY is not set")
```

### 3.3 `backend/app/deps.py` (21 lines)

FastAPI dependency injection helpers — pull singletons from `app.state`:

```python
def get_rag(request: Request) -> RAGPipeline:
    return request.app.state.rag

def get_engine(request: Request) -> QueryEngine:
    return request.app.state.engine

def get_curriculum(request: Request) -> CurriculumManager:
    return request.app.state.curriculum

def get_saved_content(request: Request) -> SavedContentManager:
    return request.app.state.saved_content
```

Used in routers like:
```python
async def my_route(rag: RAGPipeline = Depends(get_rag)): ...
```

### 3.4 `backend/app/validation.py` (106 lines)

**Input sanitization and security boundary.** Key components:

**Constants:**
```python
MAX_COURSE_CODE_LENGTH = 20
MAX_SESSION_ID_LENGTH = 50
MAX_TOPIC_LENGTH = 100
MAX_QUESTION_LENGTH = 1000
MAX_COURSE_NAME_LENGTH = 100
MAX_DESCRIPTION_LENGTH = 500
MAX_LANGUAGE_LENGTH = 20
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15MB
```

**ID sanitization (`sanitize_id`):**
- Empty input → returns `"default"`
- Replaces non-alphanumeric chars with underscores
- Prevents path traversal (`../../../etc/passwd` → `id__________etc_passwd`)
- Truncates to 50 chars

**Injection detection (used in prompt construction):**
Regex patterns for prompt injection attempts:
```python
INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules)", ...),
    re.compile(r"disregard\s+(the\s+)?(previous|prior|above|system)", ...),
    re.compile(r"forget\s+(everything|all|your\s+instructions)", ...),
    re.compile(r"you\s+are\s+now\s+", ...),
    re.compile(r"new\s+(instructions|rules|system\s+prompt)", ...),
    re.compile(r"act\s+as\s+(if|a|an)\s+", ...),
    re.compile(r"</?(system|assistant|user)>", ...),
    re.compile(r"\[/?(INST|SYS)\]", ...),
    re.compile(r"reveal\s+(your\s+)?(system\s+prompt|instructions)", ...),
]
```
`sanitize_student_query()` strips role-injection tokens and replaces override phrases with `[filtered]` so the LLM sees the attempt was made.

### 3.5 `backend/app/schemas.py` (84 lines)

Pydantic models for request/response validation:

```python
class QueryRequest(BaseModel):
    question: str = Field(..., max_length=1000)
    course_code: str = Field("BAECE102", max_length=20)
    session_id: str = Field("default", max_length=50)
    top_k: int = Field(5, ge=1, le=20)
    language: str = Field("English", max_length=20)
    mastery: float | None = Field(None, ge=0.0, le=1.0)

class PaperRequest(BaseModel):
    course_code: str = Field(..., max_length=20)
    total_marks: int = Field(100, ge=1, le=500)
    difficulty: str = Field("Medium", max_length=20)
    topics: List[str] = []
    top_k: int = Field(10, ge=1, le=50)

class CourseCreate(BaseModel):
    course_code: str = Field(..., max_length=20)
    course_name: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)
    icon: str = Field("📚", max_length=10)

class FlashcardRequest(BaseModel):
    course_code: str = Field(..., max_length=20)
    topic: str = Field(..., max_length=100)
    count: int = Field(5, ge=1, le=20)

class QuizRequest(BaseModel):
    course_code: str = Field(..., max_length=20)
    topic: str = Field(..., max_length=100)
    count: int = Field(5, ge=1, le=20)
```

Note: `flashcards.py` and `quiz.py` routers do NOT have response models — they return raw JSON from the LLM.

---

## 4. Backend: Core Modules

### 4.1 `backend/app/rag.py` (380 lines) — RAGPipeline

The **central vector storage and retrieval class**. Everything routes through this.

**`__init__` (lines 17-25):**
Reads all settings: `top_k`, `chunk_size`, `overlap`, `image_max_batch`, `image_max_per_pdf`, `rrf_k`, `ef_search`.

**`ingest()` (lines 27-83) — Text chunk ingestion:**
1. `clean_text()` — normalizes whitespace, preserves `[Page X]` markers
2. `chunk_text()` — splits into 512-token overlapping chunks at sentence boundaries
3. Batch-embeds all chunks via `client.embed_text_batch()`
4. Gets SurrealDB connection via `await get_db()`
5. For each chunk: extracts page number, removes `[Page X]` markers from stored text
6. Builds `chunk_data` dict with course_code, source_title, topic, page, text, embedding, content_type
7. Bulk inserts via SurrealDB: `INSERT INTO text_chunk $chunks`

**`ingest_images()` (lines 85-139) — Image chunk ingestion:**
1. Validates base64 strings (must be string, >=100 chars)
2. Caps at `image_max_per_pdf` (50)
3. Batch-embeds via `client.embed_images()` (5 per batch)
4. Inserts into `image_chunk` table with additional fields: `mime_type`, `image_size_kb`

**`ingest_pdf()` (lines 141-212) — Full PDF ingestion:**
1. Hashes file via `calculate_file_hash()` (SHA-256)
2. Checks `document` table for duplicate hash → returns `"already_ingested"` if exists
3. Calls `pdf_extractor.extract_all_pages()` — gets text + images per page
4. Wraps text in `[Page N]` markers for page tracking
5. Calls `self.ingest()` for text, `self.ingest_images()` for images
6. Records document in `document` table: course_code, filename, content_hash, created_at

**`retrieve()` (lines 214-322) — Hybrid search (the core retrieval):**

This is the **most important method**. Flow:

1. **Text vector search** (SurrealDB HNSW):
   ```sql
   SELECT *, vector::similarity::cosine(embedding, $query_vec) AS similarity
   FROM text_chunk
   WHERE course_code = $course
   AND embedding <|{k}, {ef_search}|> $query_vec
   ```
   Applies `RAG_MIN_SIMILARITY` threshold (0.4).
   Converts similarity to distance: `distance = 1.0 - similarity`

2. **BM25 text search** (SurrealDB fulltext):
   ```sql
   SELECT *, search::score(0) AS bm25_score
   FROM text_chunk
   WHERE course_code = $course
   AND text @0@ $query
   LIMIT {k}
   ```

3. **Reciprocal Rank Fusion (RRF):**
   ```python
   scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (rrf_k + rank + 1)
   ```
   Merges vector and BM25 results into a single ranked list.

4. **Image vector search** — same as text vector but on `image_chunk` table.

5. **Combination:** Text + image results concatenated, first `k*2` returned.

**`get_course_stats()` (lines 324-355):**
Counts text_chunks, image_chunks, groups by topic, lists distinct source_titles.

**Other methods:** `delete_course()`, `count_chunks()`, `list_courses()` — all straightforward SurrealDB queries.

### 4.2 `backend/app/query_engine.py` (294 lines) — QueryEngine

**The RAG pipeline orchestrator.** Builds prompts, calls LLM, enforces citations.

**`_get_gatekeeper_context()` (lines 158-169):**
Fetches document titles and curriculum text for the gatekeeper prompt.

**`query_stream()` (lines 172-235) — SSE streaming path:**

1. **Gatekeeper check:**
   ```python
   is_relevant, enriched_query, refusal = await gatekeeper.check_and_enrich(
       query, course_code, doc_titles, curriculum_text
   )
   ```
   If irrelevant → yields `{"type": "content", "content": refusal}` and returns.

2. **Retrieval:** calls `rag_pipeline.retrieve()` with enriched query.

3. **Prompt building:**
   ```python
   messages = build_tutor_prompt(query, course_code, course_name, chunks, history, language, mastery)
   ```

4. **Strategy generation (thinking trace):**
   ```python
   strategy_text = await client.chat(strategy_prompt, temperature=0.2, max_tokens=150)
   yield {"type": "thinking", "content": strategy_text}
   ```

5. **Streaming response:**
   ```python
   async for chunk in client.stream(messages, temperature=0.3, max_tokens=1024):
       yield chunk
   ```

6. **Verification:**
   ```python
   is_valid, reason = await verifier.verify_answer(query, full_response, chunks, course_code)
   ```
   If invalid → appends warning note.

7. **Citation extraction:** `extract_cited_sources()` matches citations back to source chunks.

8. **Metadata event:** yields `{"type": "metadata", "cited_sources": ..., "chunks_retrieved": ...}`

**`query()` (lines 237-294) — Non-streaming path:**
Same flow but calls `client.chat()` (sync response). Also runs `validate_citations()` and `remove_uncited_claims()`.

**`build_tutor_system_prompt()` (lines 39-76):**
Returns a prompt that:
- Identifies the tutor as an expert in the specific course
- Adapts to student mastery level (strong/moderate/struggling/low)
- Enforces citation rules: "Every factual claim MUST include an inline citation"
- Sets safety rules: no assignment solutions, no live exam help

**`build_context_window()` (lines 79-125):**
Constructor that takes chunks + history and produces the context string:
- Separates text from image chunks
- Tags each with `<Text N: title, Slide N>` / `<Image N: title, Slide N>` XML markers
- Builds a "VALID CITATIONS LIST" that the LLM must use
- Includes conversation history (last `max_turns`)

### 4.3 `backend/app/openrouter.py` (220 lines) — OpenRouterClient

**Singleton HTTP client** for all OpenRouter API calls. Uses `httpx.AsyncClient` with connection pooling.

**`__init__()` (lines 22-30):**
Creates a shared `httpx.AsyncClient` with:
```python
self._client = httpx.AsyncClient(
    timeout=120,
    limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
)
```

**`_api_post()` (lines 45-60):**
Generic POST wrapper — builds headers, sends request, handles HTTP errors:
```python
async def _api_post(self, path: str, json_body: dict, timeout: int = 30, context: str = ""):
    response = await self._client.post(f"{self.base_url}{path}", headers=self._headers(), json=json_body, timeout=timeout)
```
Returns parsed JSON or raises `ValueError` with truncated error message.

**Methods:**

| Method | LLM Calls | Purpose | Timeout |
|--------|-----------|---------|---------|
| `health_check()` | GET /models | Ping OpenRouter | 10s |
| `embed_text(text)` | 1 POST | Single text → embedding vector | 30s |
| `embed_text_batch(texts)` | 1 POST | Batch texts → embedding vectors | 60s |
| `embed_images(items, batch_size)` | N POSTs | Batch images (5/batch) → embeddings | 180s/batch |
| `embed_image(text)` | 1 POST | Text query → image-space embedding | 30s |
| `chat(messages)` | 1 POST | Chat completion | 120s |
| `stream(messages)` | 1 POST SSE | Streaming chat completion | 120s |
| `chat_with_schema(messages, schema)` | 1 POST | Structured JSON output via response_format | 120s |

**`embed_images()` (lines 86-110):**
Splits items into batches of `max_batch_size` (5), calls `_embed_image_batch()` for each. Failed batches are skipped (not retried), count incremented.

**`_embed_image_batch()` (lines 112-135):**
Builds multimodal input arrays:
```python
content = []
content.append({"type": "text", "text": text})
content.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64_str}"}})
inputs.append({"content": content})
```
Detects 26MB payload limit errors with specific message matching.

**`chat()` (lines 144-158):**
Sends to `/chat/completions`. Disables thinking by default (`thinking: {"type": "disabled"}`).

**`stream()` (lines 160-193):**
SSE streaming with `self._client.stream()`. Parses `data:` lines, yields `thinking` and `content` type chunks. Handles `[DONE]` signal.

**`chat_with_schema()` (lines 195-207):**
Uses OpenRouter's `response_format` with JSON schema enforcement:
```python
"response_format": {"type": "json_object", "schema": response_schema}
```
Returns parsed JSON dict. Used by gatekeeper, verifier, and paper generator.

### 4.4 `backend/app/chunker.py` (102 lines)

**Text chunking with token awareness.**

**`token_count(text)` (lines 11-12):**
Uses `tiktoken` with `cl100k_base` encoding (OpenAI's GPT-4 tokenizer).

**`chunk_text(text, chunk_size=512, overlap_tokens=64)` (lines 14-59):**
1. Splits text on sentence boundaries (`re.split(r"(?<=[.!?])\s+", text)`)
2. Accumulates sentences until token count exceeds `chunk_size`
3. Creates overlap: keeps last 3 sentences (up to ~200 chars) for context continuity
4. Returns list of `(chunk_text, start_char, end_char)` tuples

**`clean_text(text)` (lines 62-73):**
- Preserves `[Page X]` markers through a temp-replace mechanism (`__PAGE_X__`)
- Collapses whitespace, strips control characters, removes bare "Page N" strings, fixes hyphenated line breaks

**`extract_page_for_chunk(chunk_text, full_text, start_index)` (lines 76-102):**
Finds the last `[Page X]` marker before or at the chunk's start position. Returns page number or defaults to 1.

### 4.5 `backend/app/pdf_extractor.py` (108 lines)

**PDF text and image extraction** using `pypdf`.

**Magic byte detection (lines 23-51):**
```python
JPEG_MAGIC = b"\xFF\xD8\xFF"
PNG_MAGIC = b"\x89\x50\x4E\x47"
GIF_MAGIC = b"\x47\x49\x46\x38"
BMP_MAGIC = b"\x42\x4D"
WEBP_MAGIC = b"\x57\x45\x42\x50"  # (detected via RIFF container)
```

`detect_mime()` checks first bytes and returns the MIME type. Everything else is rejected.

**`_extract_page_images(page)` (lines 69-96):**
1. Gets `/Resources` → `/XObject` from PDF page
2. For each `XObject` with `/Subtype == /Image`:
   - Calls `xobj.get_data()` to get raw bytes
   - Validates with `detect_mime()` (must be >1000 bytes and pass magic byte check)
   - base64 encodes and wraps in `ImageContent` dataclass

**`extract_all_pages(source)` (lines 99-108):**
Reads PDF (from path or bytes), iterates pages, extracts text + images per page.

### 4.6 `backend/app/curriculum.py` (140 lines) — CurriculumManager

Manages curriculum PDFs for topic relevance checking.

**`ingest_curriculum()` (lines 9-83):**
1. Validates course code
2. Checks `document` table for duplicate content hash
3. Extracts PDF pages, builds chunks without embeddings first
4. Batch-embeds all pages
5. Inserts into `curriculum_chunk` table
6. **Auto-schema-fix feature (lines 50-69):** Catches `InternalError` about missing fields, dynamically alters the table with `ALTER TABLE curriculum_chunk FIELD {name} TYPE string`, then retries. This is a workaround for SurrealDB schema-on-write behavior.

**`check_topic_in_curriculum()` (lines 107-140):**
Two-tier search:
1. Searches `curriculum_chunk` with HNSW vector similarity → if max > `CURRICULUM_THRESHOLD` (0.6), returns True
2. Falls back to `text_chunk` (course notes) with same threshold
3. Returns False only if both miss

### 4.7 `backend/app/courses.py` (75 lines)

Course CRUD against SurrealDB's `course` table.

**`get_all_courses_data()`:** `SELECT * FROM course ORDER BY created_at DESC`

**`create_course()`:**
Checks for duplicate (note: the check logic has a bug — it accesses `existing[0]["result"]` but SurrealDB returns records differently), then calls `CREATE course CONTENT $content`.

**`update_course()`:** Builds dict of changed fields, calls `UPDATE course MERGE $data WHERE course_code = $code RETURN AFTER`.

**`delete_course()`:** Deletes from `course`, `text_chunk`, `image_chunk`, `curriculum_chunk` — manually cascading (the SurrealDB event-based cascade in `db.py` would also handle this, leading to double-delete, which is idempotent).

### 4.8 `backend/app/gatekeeper.py` (67 lines) — Gatekeeper

**LLM-based relevance filter.** Uses `chat_with_schema()` to get structured JSON:

```json
{
  "relevant": boolean,
  "enriched_query": "rewritten query or null",
  "refusal_message": "polite explanation or null"
}
```

The system prompt includes document titles and curriculum summary (first 2000 chars). If the LLM errors out, it falls back to allowing the query through (`return True, query, None`) — a safety valve to avoid blocking students when the small model fails.

### 4.9 `backend/app/verifier.py` (70 lines) — Verifier

**LLM-based answer grounding check.** Runs AFTER generating a response to verify it's accurate:

```json
{
  "valid": boolean,
  "reason": "explanation if invalid or null"
}
```

Rules:
1. If answer has info NOT in materials → invalid
2. If accurate but missing citations that ARE in materials → invalid

Fallback: returns `(True, None)` on error — again, prefer allowing unverified answers over blocking.

### 4.10 `backend/app/citation.py` (108 lines)

**Citation enforcement system.**

Key functions:

- **`parse_citation(text)`** — Extracts `(title, page)` from `[Source: Title, Slide N]` or `[Source: Title, Page N]`
- **`has_citation(text)`** — Regex check for `[Source: ...]` pattern
- **`extract_all_citations(text)`** — Returns list of all citation strings
- **`remove_uncited_claims(text)`** — Drops sentences without citations (exempts questions, short sentences <30 chars, greetings)
- **`format_citation(title, page)`** — Builds `[Source: title, Slide page]`
- **`validate_citations(response, chunks)`** — Returns `{valid, total_citations, valid_citations, coverage, details}`. A response is valid if >=80% of citations match actual source chunks

### 4.11 `backend/app/evaluator.py` (264 lines) — RAG Eval

**RAGAS-style evaluation framework** using LLM-as-judge.

**`RG` class methods:**

- **`faithfulness(response, contexts)`** — Count claims supported by contexts. Returns 0.0-1.0
- **`answer_relevancy(query, response)`** — Rates how well response addresses query (0.0-1.0)
- **`context_precision(query, chunks)`** — Fraction of retrieved chunks relevant to query
- **`context_recall(query, response, chunks)`** — Fraction of needed info captured in retrieved chunks

**`RAGASEvaluator`** — Higher-level interface with `evaluate()` (single case), `evaluate_batch()` (multiple), and `print_report()` (formatted output with pass/fail indicators against targets: faithfulness >= 0.85, others >= 0.80).

### 4.12 `backend/app/paper_generator.py` (101 lines)

**Exam paper generator** using LLM with schema enforcement.

`generate_paper()` builds a prompt with Bloom's taxonomy distribution guidelines and calls `client.chat_with_schema()`. The response schema enforces three sections: `mcq` (with 4 options + answer), `short_answer`, and `long_answer`.

### 4.13 `backend/app/chat_history.py` (31 lines)

**💀 DEAD CODE PATH.** All functions call `Database.session()` which accesses the Postgres SQLAlchemy engine. In reality, nothing is persisted — the functions always succeed silently without affecting SurrealDB.

Functions: `get_course_history()`, `add_message()`, `clear_course_history()`.

### 4.14 `backend/app/analytics.py` (118 lines)

**💀 DEAD CODE PATH.** Same issue as chat_history — writes to Postgres via `AnalyticsStore`. The data is collected but never retrievable from SurrealDB.

Functions: `log_query()`, `get_unanswered_questions()`, `get_coverage()`, `get_analytics()`, `get_all_questions()`.

Notable: The analytics router imports these functions, so calling `/analytics` will try to query Postgres, get empty results, and return them.

### 4.15 `backend/app/saved_content.py` (45 lines)

**💀 DEAD CODE PATH.** Manages flashcard and quiz persistence via Postgres.

Methods: `save_flashcards()`, `get_saved_flashcards()`, `delete_flashcards()`, `save_quiz()`, `get_saved_quizzes()`, `delete_quiz()`.

Each method opens a `Database.session()`, calls the corresponding store, and formats the response.

---

## 5. Backend: Routers (API Layer)

### 5.1 `backend/app/routers/query.py` (149 lines)

| Method | Path | Handler | Dependencies |
|--------|------|---------|--------------|
| `GET` | `/health` | `health()` | None — checks SurrealDB + Postgres + OpenRouter |
| `GET` | `/stats` | `get_stats()` | `rag: RAGPipeline` |
| `GET` | `/chunks` | `get_chunks()` | `rag: RAGPipeline` |
| `POST` | `/query-stream` | `query_stream()` | `engine: QueryEngine` |
| `POST` | `/query` | `query()` | `engine: QueryEngine` |

**`/health`** (lines 22-43):
Checks all three backends:
- `Database.health_check()` (💀 Postgres)
- `SurrealDBManager.health_check()`
- `client.health_check()` (OpenRouter)
Returns `"ok"` if all pass, `"degraded"` otherwise.

**`/stats`** (lines 46-50):
Calls `rag.get_course_stats(course_code)` — returns chunk counts, topics, documents.

**`/chunks`** (lines 53-74):
Debug endpoint — retrieves raw chunks and returns as `ChunkItem` list with score = `1 - distance`.

**`/query-stream`** (lines 77-115):
SSE streaming endpoint:
1. Validates/sanitizes inputs
2. Gets chat history (💀 Postgres — returns empty)
3. Yields SSE events: `data: {"type": "content", "content": "..."}`
4. After streaming: logs query + saves messages (💀 Postgres — silently fails)
5. Returns `StreamingResponse(media_type="text/event-stream")`

**`/query`** (lines 118-149):
Same as stream but returns complete JSON response. Also logs query + saves messages.

**Notable:** Both query endpoints have **no auth check**. No `Depends(get_current_user)`.

### 5.2 `backend/app/routers/auth.py` (83 lines)

| Method | Path | Handler | Dependencies |
|--------|------|---------|--------------|
| `POST` | `/auth/register` | `register()` | None |
| `POST` | `/auth/login` | `login()` | None (uses `OAuth2PasswordRequestForm`) |

**`/auth/register`** (lines 38-68):
1. Validates role ∈ {student, faculty, admin}
2. Validates password length >= 8
3. Checks existing user (💀 Postgres — always returns None, so registration always proceeds)
4. Creates user via `UserStore.create()` (💀 Postgres — never persists)
5. Returns JWT token

**`/auth/login`** (lines 71-83):
1. Gets user by email (💀 Postgres — never finds anyone)
2. Verifies password (always fails since no users exist)
3. Returns 401 "Incorrect email or password"

**Critical:** Due to the dead Postgres layer, **registration appears to succeed but no user is ever created.** Login always fails.

### 5.3 `backend/app/routers/ingestion.py` (89 lines)

| Method | Path | Handler | Dependencies |
|--------|------|---------|--------------|
| `POST` | `/ingest` | `ingest_pdf()` | `rag: RAGPipeline` |
| `POST` | `/curriculum` | `upload_curriculum()` | `curriculum: CurriculumManager` |

**`/ingest`** (lines 22-56):
1. Validates course code, sanitizes topic
2. Checks file extension (.pdf only)
3. Reads file, checks size < 15MB
4. Writes to temp file at `/tmp/ingest_{uuid}.pdf`
5. Calls `rag.ingest_pdf()` which handles chunking, embedding, and storage
6. Cleans up temp file in `finally` block
7. Returns `{text_chunks, image_chunks, total_chunks, ...}`

**`/curriculum`** (lines 59-89):
Same pattern — validate, temp file, `curriculum.ingest_curriculum()`, cleanup.

### 5.4 `backend/app/routers/quiz.py` (83 lines)

| Method | Path | Handler | Dependencies |
|--------|------|---------|--------------|
| `POST` | `/quiz` | `generate_quiz()` | `rag: RAGPipeline` |
| `POST` | `/quiz/save` | `save_quiz()` | `saved_content: SavedContentManager` |
| `GET` | `/quiz/saved` | `get_saved_quizzes()` | `saved_content: SavedContentManager` |
| `DELETE` | `/quiz/saved/{quiz_id}` | `delete_saved_quiz()` | `saved_content: SavedContentManager` |

**`/quiz`** (lines 14-51):
1. Validates course code, sanitizes topic
2. Retrieves relevant chunks (top_k=10)
3. Calls LLM to generate quiz questions as JSON
4. Parses via `safe_json_parse()` (fragile — LLM can return malformed JSON)
5. Returns raw array of question objects

The prompt requests 6 fields per question: `question`, `options` (array of 4), `correct_index`, `explanation`, `user_answer_index` (-1), `is_correct` (false).

### 5.5 `backend/app/routers/flashcards.py` (92 lines)

| Method | Path | Handler | Dependencies |
|--------|------|---------|--------------|
| `POST` | `/flashcards` | `generate_flashcards()` | `rag: RAGPipeline` |
| `POST` | `/flashcards/save` | `save_flashcards()` | `saved_content: SavedContentManager` |
| `GET` | `/flashcards/saved` | `get_saved_flashcards()` | `saved_content: SavedContentManager` |
| `DELETE` | `/flashcards/saved/{set_id}` | `delete_saved_flashcards()` | `saved_content: SavedContentManager` |

Same pattern as quiz router. The `safe_json_parse()` function is shared between both files.

### 5.6 `backend/app/routers/courses.py` (73 lines)

| Method | Path | Handler | Dependencies |
|--------|------|---------|--------------|
| `GET` | `/courses` | `list_courses()` | `rag: RAGPipeline` |
| `POST` | `/courses` | `create_new_course()` | None |
| `PUT` | `/courses/{code}` | `edit_course()` | None |
| `DELETE` | `/courses/{code}` | `remove_course()` | None |
| `GET` | `/curriculum/topics` | `get_course_topics()` | `curriculum: CurriculumManager` |
| `GET` | `/curriculum` | `list_curriculum_files()` | `curriculum: CurriculumManager` |

**`/courses` GET** (lines 13-21):
Gets all courses from SurrealDB, enriches each with doc_count and chunk_count from rag stats.

**`/courses` POST/PUT/DELETE** (lines 24-56):
All call SurrealDB functions from `courses.py`.

### 5.7 `backend/app/routers/analytics.py` (35 lines)

| Method | Path | Handler |
|--------|------|---------|
| `GET` | `/analytics` | `analytics()` |
| `GET` | `/analytics/unanswered` | `unanswered()` |
| `GET` | `/analytics/coverage` | `coverage()` |
| `GET` | `/questions` | `questions()` |

All 💀 dead Postgres calls. These endpoints will always return empty arrays.

### 5.8 `backend/app/routers/chat.py` (33 lines)

| Method | Path | Handler |
|--------|------|---------|
| `GET` | `/chat-history` | `get_history()` |
| `POST` | `/chat-history` | `save_chat_message()` |
| `DELETE` | `/chat-history` | `clear_history()` |

All 💀 dead Postgres calls.

### 5.9 `backend/app/routers/paper.py` (37 lines)

| Method | Path | Handler | Dependencies |
|--------|------|---------|--------------|
| `POST` | `/generate-paper` | `create_paper()` | `rag: RAGPipeline` |

Retrieves chunks, calls `paper_generator.generate_paper()`, returns the generated paper object.

---

## 6. Backend: Database Layer

### 6.1 `backend/app/db.py` (168 lines) — SurrealDB Connection Manager

**SurrealDBManager** is a singleton class managing a single `AsyncSurreal` connection.

**Connection flow (`get_db()`):**
1. Acquires `asyncio.Lock` to prevent concurrent initialization
2. Returns existing instance if already connected
3. Retries up to 5 times with 2s delay between attempts
4. Creates `AsyncSurreal(url)`, calls `connect()`, `signin({user, pass})`, `use(ns, db)`
5. Initializes schema via `_init_schema()`
6. Connection timeout: 10s per attempt

**Schema (`_init_schema()`) — lines 88-160:**

Tables defined:

| Table | Type | Key Fields | Indexes |
|-------|------|-----------|---------|
| `text_chunk` | SCHEMAFULL | course_code, text, embedding (array<float>), source_title, topic, page, content_type | FULLTEXT BM25 on `text`, HNSW DIMENSION 2048 COSINE on `embedding`, index on `course_code` |
| `image_chunk` | SCHEMAFULL | + mime_type, image_size_kb | HNSW DIMENSION 2048 COSINE on `embedding`, index on `course_code` |
| `curriculum_chunk` | SCHEMAFULL | Same as text_chunk | HNSW DIMENSION 2048 COSINE, index on `course_code` |
| `course` | SCHEMAFULL | course_code, course_name, description, icon, created_at | UNIQUE index on `course_code` |
| `document` | SCHEMAFULL | course_code, filename, content_hash, created_at | UNIQUE index on `content_hash` |

**Cascade delete event (lines 145-149):**
```sql
DEFINE EVENT IF NOT EXISTS course_cascade_delete ON TABLE course WHEN $event = "DELETE" THEN {
    DELETE text_chunk WHERE course_code = $before.course_code;
    DELETE image_chunk WHERE course_code = $before.course_code;
    DELETE curriculum_chunk WHERE course_code = $before.course_code;
};
```

**Health check:** `INFO FOR DB` query, returns True/False.

**Error handling:** Schema `"already exists"` errors are caught and logged as info — SurrealDB's `IF NOT EXISTS` doesn't always suppress duplicates.

### 6.2 `backend/app/database.py` (105 lines) — 💀 Dead SQLAlchemy

Full async Postgres engine setup with:
- Connection pooling (size=10, overflow=20, timeout=30)
- `pool_pre_ping=True` for stale connection detection
- Session factory with `expire_on_commit=False`
- Transaction management with commit/rollback
- Health check via `SELECT 1`
- `wait_ready()` with 5 retries, 2s delay

**Not used anywhere.** The models and stores below it are never instantiated.

### 6.3 Models (`app/models/`) — 💀 Dead ORM Models

SQLAlchemy declarative models. All follow the same pattern:

```python
class TableName(Base):
    __tablename__ = "table_name"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # ... fields ...
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

Five models:
- **`User`** — `users` table: email (unique), hashed_password, role
- **`ChatMessage`** — `chat_history` table: course_code, session_id, role, content, timestamp. Compound index on (course_code, session_id)
- **`FlashcardSet`** — `flashcard_sets` table: course_code, topic, cards (JSON)
- **`Quiz`** — `quizzes` table: course_code, topic, questions (JSON), score, total
- **`QueryLog`** — `query_logs` table: course_code, question, response_preview, out_of_scope, cited_sources (JSON)

### 6.4 Stores (`app/stores/`) — 💀 Dead CRUD Stores

Each store takes an `AsyncSession` in `__init__` and provides async CRUD methods. All use SQLAlchemy ORM patterns (SELECT, INSERT, DELETE via model classes).

---

## 7. Backend: Auth Layer

### 7.1 `backend/app/auth.py` (126 lines)

**Password hashing:**
```python
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
```
Provides `hash_password(plain) → str` and `verify_password(plain, hashed) → bool`.

**JWT tokens:**
- `create_access_token(data, expires_minutes)` — encodes dict with `exp` claim, signs with `JWT_SECRET`
- `decode_token(token)` — decodes and verifies, raises 401 on failure

**`get_current_user` dependency (lines 87-112):**
```python
async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(401)
    payload = decode_token(token)
    email = payload.get("sub")
    user = await get_user_by_email(email)  # 💀 Postgres — always returns None
    return user
```
**Never actually wired on any route.** The `auto_error=False` parameter means FastAPI won't reject requests without tokens.

**`require_role` factory (lines 115-126):**
```python
def require_role(*allowed_roles: str):
    async def _checker(user = Depends(get_current_user)):
        if user.get("role") not in allowed_roles:
            raise HTTPException(403)
        return user
    return _checker
```
Never used anywhere.

---

## 8. Backend: Tests

### 8.1 `tests/conftest.py` (34 lines)

Pytest configuration:
- Sets `CHROMA_PATH`, `SURREAL_NS`, `SURREAL_DB` env vars to test values
- Creates `surreal_db` fixture (function-scoped) — connects to SurrealDB, yields, closes
- Creates `cleanup_surreal` fixture (autouse) — removes all test tables after each test

**Tests require a running SurrealDB instance.** No mocks for the database layer.

### 8.2 `tests/test_rag.py` (222 lines)

Six test classes:

**TestChunking (5 tests):**
- `test_clean_text_removes_whitespace` — tabs/newlines removed
- `test_clean_text_removes_page_numbers` — "Page 5" stripped but `[Page X]` markers preserved
- `test_chunk_text_empty` — returns `[]`
- `test_chunk_text_small` — returns 1 chunk
- `test_chunk_text_produces_multiple` — 50 sentences → multiple chunks, each chunk is 3-tuple

**TestCitation (7 tests):**
- Citation detection, extraction, formatting, validation against known chunks
- Tests halluncinated citations (source doesn't match)
- Tests empty citations → `valid: False`

**TestQueryEngine (7 tests):**
- System prompt includes course info and adapts to mastery level
- Context window renders text chunks, image chunks, and mixed correctly
- History truncation works (>max_turns shows summary)
- `build_tutor_prompt()` returns correct message structure

**Integration tests (4 async tests):**
- `test_ingest_text_chunks` — ingest text → verify chunks > 0
- `test_retrieve_returns_chunks` — ingest + retrieve → at least 1 result
- `test_stats_includes_content_types` — ingest → stats show text_chunks >= 1
- `test_count_and_list_courses` — full CRUD lifecycle: ingest → count → list → delete

### 8.3 `tests/test_validation.py` (53 lines)

7 tests for `sanitize_id()` and `validate_id()`:
- Basic valid IDs pass through
- Empty → "default"
- Special chars → replaced with underscores
- Leading dot/underscore → prepend "id_"
- Very long → truncated to 50
- Path traversal → sanitized
- `validate_id()` rejects empty, special chars, too-long

### 8.4 `tests/test_api_limits.py` (48 lines)

3 integration tests using `TestClient`:
- File > 15MB → 413 with "File size exceeds limit"
- File < 15MB passes through middleware (may fail later at pypdf, but not 413)
- Same test for `/ingest` endpoint

### 8.5 `tests/test_db_logic.py` (174 lines)

**Requires SurrealDB + patches for OpenRouter and PDF extraction.**

Fixtures:
- `mock_client` — patches `app.curriculum.client` to return dummy embeddings
- `mock_pdf_extractor` — patches `extract_all_pages` to return 3 pages of text

Tests:
- `test_surreal_connection` — `RETURN 1` → `1`
- `test_schema_initialization` — `INFO FOR DB` shows course, text_chunk, chat_history
- `test_course_crud` — create → read → update → delete cycle against SurrealDB
- `test_chat_history_ops` — create message → read → verify fields
- `test_curriculum_ingestion_and_retrieval` — ingest → list → topics → check_topic_in_curriculum
- `test_curriculum_missing_field_auto_fix` — tests the auto-schema-fix feature (incomplete test — the `pass` at line 135 means it does nothing)
- `test_chat_history_manager` — add_message → get_course_history → clear_course_history
- `test_analytics_logging` — log_query → read from query_log table

---

## 9. Frontend: Production (`frontend/`)

### Architecture

- **Next.js 16** with App Router
- **TypeScript 5.x** with `strict: true`
- **Tailwind CSS v4** via PostCSS (`@tailwindcss/postcss`)
- **Dockerized** with multi-stage build and `output: 'standalone'`
- **No auth** — all pages are public
- **Zero mock data** — every page fetches from the backend

### Pages

| Route | File | What It Does | API Calls |
|-------|------|-------------|-----------|
| `/` | `page.tsx` | Student dashboard: lists courses from backend, shows enrollment count, progress rings derived from question keywords, "continue where you left off" | `GET /courses`, `GET /questions?course_code=...` |
| `/chat?course=...` | `chat/page.tsx` | AI Tutor: message input, SSE stream rendering, thinking indicator, cited sources panel, session history sidebar, clear session button | `POST /query-stream`, `GET /chat-history`, `DELETE /chat-history` |
| `/progress` | `progress/page.tsx` | Learning progress: weak areas (from unanswered questions), suggested revision topics, session history grouped by date | `GET /courses`, `GET /questions`, `GET /analytics`, `GET /curriculum/topics` |
| `/quiz?course=...` | `quiz/page.tsx` | Quiz: generate, take (click answers), save, review saved, delete saved | `POST /quiz`, `GET /quiz/saved`, `POST /quiz/save`, `DELETE /quiz/saved/[id]` |
| `/flashcards?course=...` | `flashcards/page.tsx` | Flashcards: generate, flip, navigate (prev/next), save set, load saved, delete | `POST /flashcards`, `GET /flashcards/saved`, `POST /flashcards/save`, `DELETE /flashcards/saved/[id]` |
| `/faculty` | `faculty/page.tsx` | Faculty dashboard: list courses, create new course (modal), delete course | `GET /courses`, `POST /courses`, `DELETE /courses/[code]` |
| `/faculty/generate` | `faculty/generate/page.tsx` | Paper generator: course select, topic input, total marks, difficulty, Bloom levels, generate button, paper preview with copy/print | `POST /generate-paper` |
| `/faculty/analytics` | `faculty/analytics/page.tsx` | Analytics dashboard: top questions list, weak topics tag cloud, questions/day bar chart, recent questions table | `GET /analytics?course_code=...` |
| `/faculty/course/[code]` | `faculty/course/[code]/page.tsx` | Course detail with 4 tabs: Materials (list curriculum, upload PDF, ingest), Analytics, Unanswered questions, Coverage stats | `GET /courses`, `GET /stats`, `GET /curriculum`, `POST /ingest`, `POST /curriculum`, `GET /analytics`, `GET /analytics/unanswered`, `GET /analytics/coverage` |

### API Client (`lib/api.ts`)

Simple 18-line fetch wrapper — no Bearer token, no auth headers, JSON-only. All API calls go through a shared `API_BASE` from `NEXT_PUBLIC_API_URL` env var.

### Components

Only 1: `Navbar.tsx` — simple top navigation bar.

---

## 10. Frontend: Experimental (`new_frontend/`)

### Architecture

- **Next.js 16.2.9** with App Router
- **TypeScript 6.0.3** with `strict: false` + `ignoreBuildErrors: true`
- **Pure CSS** — no Tailwind, no CSS-in-JS. 366-line `globals.css` design system
- **CSS Modules** — 22 component `.module.css` files + 2 page `.module.css` files
- **Dark theme** — `--color-background: #13131b`, 40+ color tokens
- **Mock data** — `mockData.ts` (176 lines, 24 exports) powers 13/14 pages
- **20 reusable components** — rich UI library with AppShell/Sidebar/TopBar

### Design System (`globals.css`)

**Color tokens (40+):**
```css
--color-background: #13131b;       /* Main background */
--color-surface-lowest: #181820;   /* Elevation levels (0-5) */
--color-surface-highest: #282840;
--color-primary: #c0c1ff;          /* Purple accent */
--color-secondary: #8cd4b0;        /* Green */
--color-tertiary: #f4a8d0;         /* Pink */
--color-error: #e06c75;
--color-admin: var(--color-primary);
--color-professor: #c4a0ff;        /* Purple for faculty role */
--color-student: #f0c050;          /* Yellow for student role */
```

**Typography scale (7 presets):**
- `--text-headline-xl: 32px` through `--text-mono-md: 14px`

**Spacing rhythm:** 8px base unit, 9-step scale (`--space-1: 8px` through `--space-10: 80px`)

**Component classes:** Auth card, form inputs, buttons, role tabs with animated slider.

### API Client (`lib/api.js`)

30 lines. Only 2 functions:

```javascript
export async function login(email, password) {
  const formData = new URLSearchParams({ username: email, password });
  return request("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: formData,
  });
}

export async function register(email, password, role = "student") {
  return request("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, role }),
  });
}
```

**No Bearer token support.** The private `request()` helper returns parsed JSON or throws `Error(detail)`.

### Mock Data (`lib/mockData.ts`)

24 named exports covering all non-login pages. Key exports:

```typescript
mockStudentUser, mockFacultyUser, mockAdminUser  // User profiles
mockStudentStats                                   // Mastery 72%, streak, topics, quizzes
mockStudentCourses / studentCourses                // 3 courses (aliases — same array)
mockFacultyCourses                                 // 2 courses
mockFacultyStats, mockFacultyActivity              // Faculty stats + recent actions
studentActivity                                    // Timeline items
chatMessages                                       // 1 mock Q&A with cited sources
adminStats, adminUsers, platformActivity, recentSignups  // Admin dashboard data
progressStats, topicsBreakdown, recommendedRevision       // Student progress
generateSections, generatedPaper                          // Paper generator
```

### Pages

**14 routes total.** Only 1 (`/` login) uses the real API. Remaining 13 use mock data or are placeholders:

| Route | Status | Data Source |
|-------|--------|-------------|
| `/` (login) | ✅ Functional | Real API (`/auth/login`) |
| `/student/dashboard` | ✅ Renders | Mock (`mockStudentStats`, `mockStudentCourses`) |
| `/student/quiz` | ⛔ Placeholder | "Under development" |
| `/student/progress` | ✅ Renders | Mock (`progressStats`, `topicsBreakdown`, `recommendedRevision`) |
| `/student/profile` | ⛔ Placeholder | Just text |
| `/student/flashcards` | ⛔ Placeholder | "Under development" |
| `/student/courses/[code]` | ✅ Renders | Mock (`courseDetail`, `chatMessages`) |
| `/student/chat` | ⛔ Placeholder | "Coming soon" |
| `/faculty/dashboard` | ✅ Renders | Mock (`mockFacultyStats`, `mockFacultyCourses`) |
| `/faculty/generate` | ✅ Renders | Mock (`generateSections`, `generatedPaper`) |
| `/faculty/profile` | ⛔ Placeholder | Just text |
| `/faculty/course/[code]` | ✅ Renders | Local state (initialized with mock entries) |
| `/faculty/analytics` | ⛔ Placeholder | "Coming soon" |
| `/admin/dashboard` | ✅ Renders | Mock (`adminStats`, `adminUsers`, `platformActivity`) |
| `/admin/profile` | ⛔ Placeholder | Just text |

### Components

| Component | Purpose |
|-----------|---------|
| `AppShell` | Main layout — renders Sidebar + TopBar + content area |
| `Sidebar` | Navigation — role-based menu items, active state, collapse |
| `TopBar` | Top bar — page title, search, user avatar |
| `CourseCard` | Course card — title, description, color, doc count |
| `StatTile` | Metric tile — label, value, trend arrow |
| `RadialProgress` | Circular SVG progress — percentage, label |
| `ProgressBar` | Linear progress bar — fill %, color |
| `ActivityHeatmap` | GitHub-style grid — dates, intensity levels |
| `MiniBarChart` | Small bar chart — labels, values, max height |
| `DataTable` | Table — column headers, rows, sortable |
| `Badge` | Status badge — color variants |
| `BloomPill` | Bloom's taxonomy level pill — color-coded |
| `Breadcrumbs` | Breadcrumb trail — links, current page |
| `AvatarOrInitials` | User avatar — image or initials fallback |
| `Dropzone` | File upload dropzone — click/drag state |
| `FileTypeIcon` | File type icon — pdf, image, etc. |
| `FormField` | Form field — label, input, error message |
| `CheckboxCard` | Checkbox card — selected state |
| `RemovableSection` | Section with X button — removable items |
| `PaperPreview` | Paper preview — formatted questions, copy/print |

---

## 11. Infrastructure & Docker

### 11.1 `docker-compose.yml` (64 lines)

Four services:

**surrealdb (lines 4-12):**
```yaml
image: surrealdb/surrealdb:latest
user: root
command: start --user root --pass root surrealkv://data/surrealdb.db
ports: ["8000:8000"]
volumes: [surreal_data:/data]
```
- Persistent file mode (`surrealkv://`)
- Hardcoded credentials (root/root) — acceptable for local dev
- Runs as root — security concern for production

**backend (lines 14-37):**
```yaml
build: ./backend
ports: ["8001:8001"]
environment:
  - SURREAL_URL=ws://surrealdb:8000/rpc
  - SURREAL_USER=root, SURREAL_PASS=root
  - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
  - JWT_SECRET=${JWT_SECRET}
  - DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/adaptive_learning
depends_on: [surrealdb, postgres]
volumes: [./backend/storage:/app/storage, ./chroma_db:/app/chroma_db]
```
- Depends on both SurrealDB and Postgres (both must be healthy before backend starts)
- Mounts storage and chroma_db directories
- Env vars from host's environment (no `.env` file reference)

**frontend (lines 39-47):**
```yaml
build:
  context: ./.worktrees/phase-1-integration/new_frontend  # ⚠️ worktree path
  dockerfile: Dockerfile
ports: ["3000:3000"]
environment:
  - NEXT_PUBLIC_API_URL=http://localhost:8001
depends_on: [backend]
```
- Build context is a **git worktree** path — will fail if worktree doesn't exist
- Uses `new_frontend/` Dockerfile, not `frontend/`
- Points to host's `localhost:8001` (not docker service name) — works because both are on host network

**postgres (lines 49-58) — 💀 DEAD:**
```yaml
image: pgvector/pgvector:pg16
environment:
  - POSTGRES_DB=adaptive_learning
  - POSTGRES_USER=postgres
  - POSTGRES_PASSWORD=postgres
ports: ["5433:5432"]
volumes: [postgres_data:/var/lib/postgresql/data]
```
Runs but nothing connects to it. The `DATABASE_URL` env var in the backend references it, but no code uses that URL.

**Volumes:** `surreal_data`, `postgres_data` (both named volumes).

### 11.2 `backend/Dockerfile` (31 lines)

```dockerfile
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y build-essential ca-certificates && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8001
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
```

**Issues:**
- No `.dockerignore` — `venv/`, `__pycache__/`, `.env` all get sent to Docker context
- No non-root user — runs as root

### 11.3 `frontend/Dockerfile`

Multi-stage build with `output: 'standalone'`. Not detailed here since `docker-compose.yml` uses new_frontend's Dockerfile.

### 11.4 Setup Scripts (`setup/`)

All 3 are **broken** with the same two bugs:

| Script | Wrong Path (line) | Wrong Placeholder (line) | Dead Command (line) |
|--------|------------------|-------------------------|---------------------|
| `setup.sh` | `cp backend/.env.example` (47) | `your_api_key_here` (50) | `python main.py` (56) |
| `setup.bat` | `copy backend\.env.example` (36) | `your_api_key_here` (39) | `python main.py` (44) |
| `setup.ps1` | `Copy-Item "backend\.env.example"` (32) | `your_api_key_here` (34) | `python main.py` (38) |

**.env.example is at the repo root**, not in `backend/`. The actual placeholder string in `.env.example:2` is `your_openrouter_api_key_here`.

---

## 12. Documentation

### 12.1 `docs/API.md` (407 lines)

The most up-to-date API reference. Covers all endpoints with request/response JSON examples. Key note (line 6): "All routes are **unauthenticated** — auth endpoints exist but tokens are never validated on protected routes."

### 12.2 `docs/ARCHITECTURE.md` (164 lines)

Covers:
- Three storage systems (SurrealDB primary, ChromaDB/history, JSON legacy)
- 6-stage RAG pipeline
- Service architecture with port map
- Auth architecture
- Two frontend comparison
- Key tech debt items

### 12.3 `SPEC.md` (201 lines)

Partially outdated — references `rag_pipeline/` directory that no longer exists, says "No Docker" when Docker Compose is now used, lists only 5 API endpoints when there are 25+.

### 12.4 `CONTRIBUTING.md` (29 lines)

Basic contribution guide. Says to use `new_frontend/` for active development. References `backend/storage/` for data persistence.

### 12.5 `AGENTS.md` (50 lines)

Agent-specific guide detailing project state (MVP, ~3/10 readiness), gotchas (setup scripts broken, no CI/CD, duplicate functions, outdated SPEC.md), and developer conventions.

### 12.6 `README.md` (184 lines)

Feature list, tech stack table, project structure, quick start, Docker alternative, architecture diagrams (ASCII), quick-fix priority table, MVP limitations.

---

## 13. Dead Code Inventory

Everything that's unused or non-functional:

| File | Lines | Type | Reason |
|------|-------|------|--------|
| `backend/app/database.py` | 105 | 💀 DEAD | SQLAlchemy Postgres engine — nothing imports it |
| `backend/app/models/` (5 files) | ~84 | 💀 DEAD | ORM models — never instantiated |
| `backend/app/stores/` (5 files) | ~200 | 💀 DEAD | CRUD stores — zero callers |
| `backend/app/chat_history.py` | 31 | 💀 DEAD | Uses Postgres session (always succeeds silently) |
| `backend/app/analytics.py` | 118 | 💀 DEAD | Uses Postgres session (returns empty always) |
| `backend/app/saved_content.py` | 45 | 💀 DEAD | Uses Postgres session (saves/loads nothing) |
| `docker-compose.yml:49-58` | 10 | 💀 DEAD | Postgres service — no code connects |
| `backend/.env:6` | 1 | 💀 DEAD | `DATABASE_URL` — no code reads it |
| `backend/app/validation.py:101-106` | 6 | 💀 DEAD | `validate_filename()` — never called |
| `chroma_db/` | dir | 💀 DEAD | ChromaDB replaced by SurrealDB HNSW |
| `legacy_data/` | dir | 💀 DEAD | Old JSON storage — not migrated |
| `new_frontend/src/lib/mockData.ts` | 176 | 🧪 TEST | Only 1/14 pages wired to real API |
| `backend/app/routers/auth.py` | 83 | ⚠️ BROKEN | Register succeeds silently (Postgres dead), login always fails |
| `setup/*` (3 files) | ~140 | ⚠️ BROKEN | Wrong paths + wrong placeholders |
| `docs/SETUP.md:18` | 1 | ⚠️ BROKEN | References non-existent `setup/migrate.sh` |

Total dead code: **~750 lines of Python + 1 Docker service + 2 directories**

---

## 14. Data Flow: Complete Traces

### 14.1 Student Query (RAG) — Full Path

```
Client → POST /query
  ├── server.py:69         → router: query.router
  ├── routers/query.py:118 → validate_course_code(), sanitize_id(), sanitize_text()
  ├── routers/query.py:127 → get_course_history()  → chat_history.py:5
  │     └── Database.session()                     → 💀 returns empty list
  ├── routers/query.py:129 → engine.query(question, course_code, ...)  → query_engine.py:237
  │     ├── query_engine.py:247  → _get_gatekeeper_context(course_code)
  │     │     ├── rag.py:324     → get_course_stats() → SurrealDB count queries
  │     │     └── db.py:163      → get_db() → SurrealDB curriculum_chunk query
  │     ├── query_engine.py:248  → gatekeeper.check_and_enrich()
  │     │     ├── gatekeeper.py:42 → client.chat_with_schema()  → openrouter.py:196
  │     │     │     └── POST /chat/completions → OpenRouter API [LLM CALL 1]
  │     │     └── if LLM fails → returns (True, query, None) [fallback]
  │     ├── query_engine.py:260  → rag_pipeline.retrieve(enriched_query)
  │     │     ├── openrouter.py:74 → client.embed_text() → POST /embeddings [API CALL 2]
  │     │     ├── db.py:163        → SurrealDB: vector search text_chunk (HNSW)
  │     │     │     └── applies RAG_MIN_SIMILARITY=0.4 threshold
  │     │     ├── db.py:163        → SurrealDB: BM25 search text_chunk
  │     │     ├── RRF fusion       → merge + score + sort
  │     │     ├── openrouter.py:137 → client.embed_image(query) → POST /embeddings [API CALL 3]
  │     │     └── db.py:163        → SurrealDB: vector search image_chunk (HNSW)
  │     ├── query_engine.py:266  → build_tutor_prompt(question, chunks, history, mastery)
  │     │     ├── build_tutor_system_prompt()  → mastery-adapted prompt
  │     │     └── build_context_window()       → XML-tagged chunks + citations list + history
  │     ├── query_engine.py:276  → client.chat(messages) → POST /chat/completions [LLM CALL 4]
  │     ├── query_engine.py:278  → verifier.verify_answer()
  │     │     └── client.chat_with_schema()    → POST /chat/completions [LLM CALL 5]
  │     ├── query_engine.py:282  → validate_citations(response, chunks)
  │     │     └── citation.py:68 → extract citations → match against source chunks
  │     ├── query_engine.py:284  → remove_uncited_claims(response)
  │     │     └── citation.py:44 → drop sentences without [Source: ...]
  │     └── query_engine.py:286  → extract_cited_sources(response, chunks)
  ├── routers/query.py:139   → log_query(question, response, citations) → 💀 Postgres (silent)
  ├── routers/query.py:140   → add_message(user, question) → 💀 Postgres (silent)
  └── routers/query.py:141   → add_message(assistant, response) → 💀 Postgres (silent)
```

**Total external calls per query:** 5 (3 LLM + 2 embed embedding)
**Latency estimate:** 2-5 seconds (dominated by LLM calls)

### 14.2 PDF Ingestion — Full Path

```
Client → POST /ingest (multipart: file, course_code, topic)
  ├── server.py:72         → router: ingestion.router
  ├── routers/ingestion.py:29 → validate_course_code(), sanitize_text()
  ├── routers/ingestion.py:32 → file extension check (.pdf)
  ├── server.py:60-66       → middleware: check content-length < 15MB
  ├── routers/ingestion.py:37 → file.read() → bytes
  ├── routers/ingestion.py:38 → len(content) > MAX_FILE_SIZE → 413
  ├── routers/ingestion.py:41 → write to /tmp/ingest_{uuid}.pdf
  ├── routers/ingestion.py:44 → title = Path(file.filename).stem (sanitized)
  ├── routers/ingestion.py:47 → rag.ingest_pdf(course_code, title, temp_path, topic)
  │     ├── rag.py:150     → calculate_file_hash(temp_path) → SHA-256
  │     ├── rag.py:153     → SurrealDB: check document table for hash
  │     ├── rag.py:168     → pdf_extractor.extract_all_pages(temp_path)
  │     │     ├── pypdf.PdfReader → iterate pages
  │     │     │     └── ⚠️ SYNC OPERATION — blocks event loop
  │     │     ├── For each page:
  │     │     │     ├── page.extract_text() → string
  │     │     │     └── _extract_page_images() → iterate XObjects
  │     │     │           └── magic byte validation → ImageContent list
  │     │     └── → list[PageContent(page_num, text, images)]
  │     ├── rag.py:188     → join text parts with [Page N] markers
  │     ├── rag.py:189     → self.ingest(course_code, title, full_text, ...)
  │     │     ├── clean_text() → normalize
  │     │     ├── chunk_text() → token-aware sentence splitting
  │     │     ├── client.embed_text_batch(chunks) → POST /embeddings [API CALL]
  │     │     └── SurrealDB: INSERT INTO text_chunk $chunks
  │     ├── rag.py:192     → self.ingest_images(course_code, title, image_items, ...)
  │     │     ├── validate base64 strings
  │     │     ├── cap at image_max_per_pdf (50)
  │     │     ├── client.embed_images(items, batch_size=5) → N POSTs [API CALLS]
  │     │     └── SurrealDB: INSERT INTO image_chunk $chunks
  │     └── rag.py:196     → SurrealDB: INSERT INTO document {course, file, hash, time}
  ├── routers/ingestion.py:55 → os.remove(temp_path) [finally block]
  └── → {text_chunks, image_chunks, total_chunks, ...}
```

**⚠️ Blocking issue:** `extract_all_pages()` uses `pypdf.PdfReader` which is synchronous — blocks the async event loop for the duration of PDF parsing.

### 14.3 Quiz Generation — Full Path

```
Client → POST /quiz {course_code, topic, count}
  ├── routers/quiz.py:19  → validate_course_code(), sanitize_text()
  ├── routers/quiz.py:25  → rag.retrieve(query=topic, top_k=10)
  │     ├── embed_text() [API CALL 1]
  │     ├── SurrealDB vector search + BM25 + RRF
  │     └── embed_image() [API CALL 2]
  ├── routers/quiz.py:44  → client.chat(prompt) → POST /chat/completions [API CALL 3]
  └── routers/quiz.py:48  → safe_json_parse(response) → fragile JSON parser
```

**Total API calls:** 3 (2 embed + 1 LLM)

---

## 15. Known Gotchas & Pitfalls

### 15.1 Auth is Broken

**Symptom:** Registration appears to succeed but users aren't persisted (dead Postgres). Login always returns 401. Even if auth worked, no route validates the token.

**Root cause:** `auth.py` uses Postgres via `UserStore`. Postgres is dead code. SurrealDB is the real database.

**Fix:** Migrate `get_user_by_email()` to SurrealDB or wire a proper user table there.

### 15.2 Chat History, Analytics, Saved Content All Write to Postgres

**Symptom:** Chat messages, quiz saves, flashcard saves, and analytics queries all silently do nothing. Endpoints return `{"status": "success"}` but nothing is stored.

**Root cause:** `chat_history.py`, `analytics.py`, and `saved_content.py` all use `Database.session()` which connects to the dead Postgres engine.

**Fix:** Rewrite these modules to use SurrealDB instead of Postgres. The SurrealDB schema already has `course` table; needs `chat_history`, `query_log`, `flashcard_set`, `quiz` tables defined.

### 15.3 HNSW Dimension Mismatch Warning

**Symptom:** SurrealDB HNSW indexes are DIMENSION 2048. The Nemotron VL embedding model likely produces different dimensions.

**Root cause:** The code hardcodes 2048 in `db.py` schema but the actual model may output 1024 (image) or 384 (text) dimensions. README mentions 384/1024 but says "ignore README, the code is right" — this hasn't been verified at runtime.

**Fix:** Verify actual embedding dimensions from OpenRouter responses and match them in the schema.

### 15.4 Two Frontends = Double Maintenance

**Symptom:** Bug fixes and features must be implemented twice — once in each frontend. Different course IDs (`BAECE102` vs `bio101`), different CSS frameworks, different API clients.

**Decide:** Pick one canonical frontend. `frontend/` is production-ready (all APIs wired, strict TypeScript, Dockerized). `new_frontend/` has a richer component library but is mostly mock data.

### 15.5 Setup Scripts Don't Work

**Symptom:** Every new contributor runs `bash setup/setup.sh` and gets errors about missing file and wrong placeholder.

**Fix:** Change `cp backend/.env.example` to `cp .env.example` and `your_api_key_here` to `your_openrouter_api_key_here` in all 3 scripts. Or delete them and document manual setup in README.

### 15.6 Docker Compose Uses Worktree Path

**Symptom:** `docker compose up --build` fails because `.worktrees/phase-1-integration/new_frontend/` doesn't exist.

**Fix:** Change `docker-compose.yml:40` context to `./new_frontend` and ensure that directory has a Dockerfile.

### 15.7 Postgres Dependency Blocks Startup

**Symptom:** Backend container won't start until Postgres is healthy (which it always is, but the container wait adds 5-10s to startup).

**Fix:** Remove Postgres dependency. Also remove Postgres from health check.

### 15.8 Rate Limits Reset on Restart

**Symptom:** The `slowapi` rate limiter is in-memory — restarting the backend resets all rate limit counters. Also doesn't work across multiple workers.

**Fix:** Add Redis backend for rate limiting if horizontal scaling is needed.

### 15.9 No Request ID Correlation

**Symptom:** Logs from different requests are indistinguishable — no trace ID is propagated through the request lifecycle.

**Fix:** Add FastAPI middleware that generates X-Request-ID and includes it in all downstream calls and log entries.

### 15.10 Frontend Token Stored But Never Used

**Symptom:** Login stores `token` in `localStorage` but no subsequent API call reads it. Even if backend auth were wired, the frontend couldn't authenticate.

**Fix:** Extend API client to inject `Authorization: Bearer <token>` header from `localStorage` on every request. Add 401 handling (redirect to login).

---

*This document was generated from commit `363b183`. For the full security and code audit, see `REPOSITORY_AUDIT_REPORT.md`.*
