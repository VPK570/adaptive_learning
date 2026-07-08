# Architecture Connections (Plain Text)

All relationships between components in the Adaptive Learning Platform.

---

## 1. Frontend → Backend Connections

| From | To | How | What |
|------|----|-----|------|
| new_frontend (Next.js) | Backend (FastAPI :8001) | HTTP (fetch) | All API calls — query, courses, analytics, flashcards, quiz, auth, ingest, chat, paper |
| new_frontend | Backend | Server-Sent Events (SSE) | `/query-stream` — streaming AI tutor responses token-by-token |
| new_frontend | localStorage | browser API | `enrolled_{course_code}`, `last_question_*`, `session_id` — enrollment flags and chat state |
| new_frontend | React useState/useEffect | component lifecycle | All local component state — form inputs, chat messages, quiz answers, flip states |

---

## 2. Backend → Backend (Internal Module Dependencies)

### 2.1 Startup Initialization (server.py)

| From | To | How | What |
|------|----|-----|------|
| server.py (lifespan) | RAGPipeline | `app.state.rag = RAGPipeline()` | Creates singleton on startup |
| server.py (lifespan) | QueryEngine | `app.state.engine = QueryEngine()` | Creates singleton on startup |
| server.py (lifespan) | CurriculumManager | `app.state.curriculum = CurriculumManager()` | Creates singleton on startup |
| server.py (lifespan) | SavedContentManager | `app.state.saved_content = SavedContentManager()` | Creates singleton on startup |
| server.py | 9 routers | `app.include_router(...)` | Mounts query, courses, analytics, chat, ingestion, flashcards, quiz, paper, and auth routers |

### 2.2 Dependency Injection (deps.py)

| From | To | How | What |
|------|----|-----|------|
| deps.get_rag | app.state.rag | FastAPI Depends() | Injects RAGPipeline into route handlers |
| deps.get_engine | app.state.engine | FastAPI Depends() | Injects QueryEngine into route handlers |
| deps.get_curriculum | app.state.curriculum | FastAPI Depends() | Injects CurriculumManager into route handlers |
| deps.get_saved_content | app.state.saved_content | FastAPI Depends() | Injects SavedContentManager into route handlers |

### 2.3 Router → Service Module Calls

| Router | Calls | Purpose |
|--------|-------|---------|
| query.py | QueryEngine.query_stream(), QueryEngine.query() | AI tutor Q&A |
| query.py | RAGPipeline.get_course_stats(), retrieve(), list_courses() | Stats and retrieval |
| query.py | analytics.log_query() | Log every query for analytics |
| ingestion.py | RAGPipeline.ingest_pdf() | Upload and ingest PDFs |
| ingestion.py | CurriculumManager.ingest_curriculum() | Upload curriculum/syllabus |
| courses.py | courses.get_all_courses_data(), create_course(), update_course(), delete_course() | Course CRUD |
| courses.py | curriculum.get_curriculum_topics(), list_curriculum() | Curriculum topics |
| analytics.py | analytics.get_analytics(), get_unanswered(), get_coverage() | Dashboard data |
| chat.py | chat_history.get_messages(), add_message(), clear_session() | Chat persistence |
| flashcards.py | saved_content.save_flashcards(), get_saved_flashcards(), delete_flashcards() | Flashcard CRUD |
| flashcards.py | openrouter.client.chat() | Generate flashcards via LLM |
| quiz.py | saved_content.save_quiz(), get_saved_quizzes(), delete_quiz() | Quiz CRUD |
| quiz.py | openrouter.client.chat() | Generate quiz via LLM |
| paper.py | paper_generator.generate_paper() | Question paper generation |
| auth.py (router) | auth.hash_password(), verify_password(), create_access_token(), get_user_by_email() | Registration and login |

### 2.4 Service → Service Calls

| From | To | How | What |
|------|----|-----|------|
| QueryEngine | Gatekeeper.check_and_enrich() | Direct async call | Pre-query: check relevance + enrich query |
| QueryEngine | RAGPipeline.retrieve() | Direct async call | Hybrid search (BM25 + vector + RRF) |
| QueryEngine | RAGPipeline.get_course_stats() | Direct async call | Get document titles for gatekeeper context |
| QueryEngine | openrouter.client.chat() | Direct async call | Generate thinking strategy |
| QueryEngine | openrouter.client.stream() | Direct async call | Stream LLM response |
| QueryEngine | verifier.verify_answer() | Direct async call | Post-answer grounding check |
| QueryEngine | citation.extract_cited_sources() | Direct function call | Parse citations from response |
| QueryEngine | citation.validate_citations() | Direct function call | Check citation coverage |
| QueryEngine | citation.remove_uncited_claims() | Direct function call | Strip unsupported claims |
| QueryEngine | validation.sanitize_student_query() | Direct function call | Strip prompt injection attempts |
| RAGPipeline | chunker.chunk_text(), clean_text() | Direct function call | Split text into 512-token chunks |
| RAGPipeline | chunker.extract_page_for_chunk() | Direct function call | Map chunks back to page numbers |
| RAGPipeline | openrouter.client.embed_text(), embed_text_batch() | Direct async call | Generate text embeddings |
| RAGPipeline | openrouter.client.embed_images(), embed_image() | Direct async call | Generate image embeddings |
| RAGPipeline | pdf_extractor.extract_all_pages() | Direct async call | Extract text + images from PDF |
| RAGPipeline | db.get_db() | Direct async call | Store chunks in SurrealDB |
| CurriculumManager | pdf_extractor.extract_all_pages() | Direct async call | Extract curriculum text from PDF |
| CurriculumManager | openrouter.client.embed_text_batch() | Direct async call | Embed curriculum chunks |
| CurriculumManager | db.get_db() | Direct async call | Store curriculum chunks |
| Gatekeeper | openrouter.client.chat_with_schema() | Direct async call | Structured JSON relevance check |
| Verifier | openrouter.client.chat_with_schema() | Direct async call | Structured JSON grounding verification |
| paper_generator | openrouter.client.chat_with_schema() | Direct async call | Generate structured question paper |
| saved_content | db.get_db() | Direct async call | CRUD on flashcard_set and quiz tables |
| chat_history | db.get_db() | Direct async call | CRUD on chat_history table |
| analytics | db.get_db() | Direct async call | Query query_log for analytics |
| courses | db.get_db() | Direct async call | CRUD on course table |
| auth (auth.py) | db.get_db() | Direct async call | CRUD on users table |

---

## 3. Backend → Storage Connections

| From | To | How | What |
|------|----|-----|------|
| RAGPipeline | SurrealDB (text_chunk) | SurQL INSERT | Store text chunks with embeddings |
| RAGPipeline | SurrealDB (image_chunk) | SurQL INSERT | Store image chunks with embeddings |
| RAGPipeline | SurrealDB (document) | SurQL INSERT | Record ingestion for dedup |
| RAGPipeline | SurrealDB (course) | SurQL INSERT (via cascade event) | Course deletion cascades to chunks |
| QueryEngine | SurrealDB (query_log) | SurQL INSERT (via analytics.log_query) | Log every query |
| CurriculumManager | SurrealDB (curriculum_chunk) | SurQL INSERT | Store curriculum chunks |
| CurriculumManager | SurrealDB (document) | SurQL INSERT | Record curriculum ingestion |
| saved_content | SurrealDB (flashcard_set) | SurQL INSERT/SELECT/DELETE | Flashcard CRUD |
| saved_content | SurrealDB (quiz) | SurQL INSERT/SELECT/DELETE | Quiz CRUD |
| chat_history | SurrealDB (chat_history) | SurQL INSERT/SELECT/DELETE | Chat message CRUD |
| analytics | SurrealDB (query_log) | SurQL SELECT | Generate analytics |
| courses | SurrealDB (course) | SurQL INSERT/SELECT/UPDATE/DELETE | Course CRUD |
| auth | SurrealDB (users) | SurQL INSERT/SELECT | User registration and login |

### SurrealDB Connection Details

| Detail | Value |
|--------|-------|
| Connection string | `ws://surrealdb:8000/rpc` (docker) or `ws://localhost:8000/rpc` (dev) |
| Namespace | `adaptive_learning` |
| Database | `learning_platform` |
| Auth | `root / root` (configurable via env) |
| Connection class | `SurrealDBManager` — singleton with retry (5 attempts, 2s delay, 10s timeout) |
| Schema init | Auto-runs on first connection — defines all 10 tables, fields, indexes, and cascade events |

---

## 4. Backend → External Service Connections

| From | To | How | What |
|------|----|-----|------|
| OpenRouterClient | OpenRouter API | HTTPS POST | Text embeddings (`/embeddings`, Nemotron VL, 2048-dim) |
| OpenRouterClient | OpenRouter API | HTTPS POST | Image embeddings (`/embeddings`, multimodal, Nemotron VL, 2048-dim) |
| OpenRouterClient | OpenRouter API | HTTPS POST | Chat completions (`/chat/completions`, Nemotron 3B) |
| OpenRouterClient | OpenRouter API | HTTPS POST (streaming) | SSE streaming chat (`/chat/completions` with `stream: true`) |
| OpenRouterClient | OpenRouter API | HTTPS POST | Structured JSON output (`response_format` with JSON schema) |
| OpenRouterClient | OpenRouter API | HTTPS GET | Health check (`/models`) |

### OpenRouter Client Details

| Detail | Value |
|--------|-------|
| Base URL | `https://openrouter.ai/api/v1` |
| Auth header | `Authorization: Bearer {OPENROUTER_API_KEY}` |
| HTTP library | `httpx.AsyncClient` (connection pooling, max 100 connections, 20 keepalive) |
| Timeouts | 30s embeddings, 120s chat, 180s image batch |
| Rate limiting | Backend limits: 60 requests/minute per IP (SlowAPI) |
| Image batch | 5 images per batch, max 50 per PDF |

---

## 5. Storage → Storage Relationships (SurrealDB Schema)

### Tables and Their Relationships

| Table | References | Via | Type |
|-------|-----------|-----|------|
| text_chunk | course | `course_code` field | Foreign key (logical, not enforced) |
| image_chunk | course | `course_code` field | Foreign key (logical, not enforced) |
| curriculum_chunk | course | `course_code` field | Foreign key (logical, not enforced) |
| chat_history | course | `course_code` field | Foreign key (logical, not enforced) |
| flashcard_set | course | `course_code` field | Foreign key (logical, not enforced) |
| quiz | course | `course_code` field | Foreign key (logical, not enforced) |
| query_log | course | `course_code` field | Foreign key (logical, not enforced) |
| document | course | `course_code` field | Foreign key (logical, not enforced) |
| course | — | `course_code` (unique) | Primary table, cascade deletes to text_chunk, image_chunk, curriculum_chunk |

### Cascade Delete Behavior

```
DELETE FROM course WHERE course_code = 'X'
  → EVENT course_cascade_delete fires
    → DELETE text_chunk WHERE course_code = 'X'
    → DELETE image_chunk WHERE course_code = 'X'
    → DELETE curriculum_chunk WHERE course_code = 'X'
  (chat_history, flashcard_set, quiz, query_log, document are NOT auto-deleted)
```

### Indexes

| Table | Index Type | Field(s) |
|-------|-----------|----------|
| course | UNIQUE | `course_code` |
| users | UNIQUE | `email` |
| document | UNIQUE | `content_hash` |
| text_chunk | HNSW (2048d, cosine) | `embedding` |
| text_chunk | FULLTEXT BM25 | `text` |
| image_chunk | HNSW (2048d, cosine) | `embedding` |
| curriculum_chunk | HNSW (2048d, cosine) | `embedding` |
| All 7 course-referencing tables | STANDARD | `course_code` |

---

## 6. Auth Connections

| Step | From | To | What |
|------|------|----|------|
| 1 | Client | POST /auth/register | Sends `{email, password, role}` |
| 2 | Router (auth.py) | validation.py | Validates email format, password >= 8 chars, role ∈ {student, faculty, admin} |
| 3 | Router (auth.py) | db.get_db() | Check if email already exists in users table |
| 4 | Router (auth.py) | auth.hash_password() | bcrypt hash of plaintext password |
| 5 | Router (auth.py) | db.get_db() | INSERT into users `{email, hashed_password, role, created_at}` |
| 6 | Router (auth.py) | auth.create_access_token() | Generate JWT `{sub: email, role: ..., exp: ...}` signed with HS256 |
| 7 | Router (auth.py) | Client | Return `{access_token, token_type: "bearer", role}` |
| 8 | Client | POST /auth/login | Sends `{username: email, password}` (OAuth2 form) |
| 9 | Router (auth.py) | db.get_db() | SELECT from users WHERE email = ? |
| 10 | Router (auth.py) | auth.verify_password() | bcrypt verify |
| 11 | Router (auth.py) | auth.create_access_token() | Generate JWT |
| 12 | Router (auth.py) | Client | Return `{access_token, token_type, role}` |
| — | — | — | **IMPORTANT**: No route currently uses `Depends(get_current_user)`. Auth endpoints work and return tokens, but tokens are never validated on any other route. |

### JWT Structure

| Field | Source | Example |
|-------|--------|---------|
| sub | User email | `student@vit.ac.in` |
| role | User role | `student` |
| exp | Current time + JWT_EXPIRE_MINUTES (default 1440 = 24h) | `1719700000` |
| Secret | JWT_SECRET env var | (256-bit hex string) |
| Algorithm | JWT_ALGORITHM env var | `HS256` |

---

## 7. RAG Pipeline — Internal Data Flow

```
Student Query
     │
     ▼
┌─ Gatekeeper ──────────────────────────────────────────────┐
│  Input: query, course_code, doc_titles, curriculum_text    │
│  LLM: chat_with_schema() → {relevant, enriched_query,     │
│                             refusal_message}               │
│  Output: (is_relevant: bool, enriched_query: str,          │
│           refusal: str|None)                               │
│  Fallback: returns (True, query, None) if LLM fails        │
└──────────────────────┬─────────────────────────────────────┘
                       │ (if relevant)
                       ▼
┌─ RAGPipeline.retrieve ────────────────────────────────────┐
│  Input: enriched_query, course_code, top_k                 │
│                                                             │
│  Step 1: Embed query → openrouter.client.embed_text()      │
│  Step 2: Vector search → SurrealDB HNSW (cosine, threshold │
│           0.4) on text_chunk                                │
│  Step 3: BM25 search → SurrealDB fulltext on text_chunk    │
│  Step 4: RRF fusion → Combine vector + BM25 scores         │
│           (RRF_K = 60)                                      │
│  Step 5: Image search → SurrealDB HNSW on image_chunk      │
│           (threshold 0.4)                                   │
│  Output: list of chunks {source_title, page, text,          │
│           embedding, content_type, similarity}             │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       ▼
┌─ QueryEngine.build_tutor_prompt ──────────────────────────┐
│  Input: query, chunks, history, language, mastery          │
│                                                             │
│  - sanitize_student_query() → strip injection attempts     │
│  - build_tutor_system_prompt() → mastery-adaptive prompt   │
│  - build_context_window() → text chunks + image chunks +   │
│    valid citations list + conversation history              │
│  Output: [{role: "system", content: ...},                   │
│            {role: "user", content: ...}]                    │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       ▼
┌─ LLM Call ────────────────────────────────────────────────┐
│  Step 1: Thinking strategy → client.chat(temperature=0.2, │
│           max_tokens=150)                                   │
│           → yields {"type": "thinking", "content": ...}    │
│                                                             │
│  Step 2: Main answer → client.stream(temperature=0.3,     │
│           max_tokens=1024)                                  │
│           → yields {"type": "content", "content": ...}     │
│             (token-by-token via SSE)                        │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       ▼
┌─ Verifier ────────────────────────────────────────────────┐
│  Input: query, full_response, chunks, course_code           │
│  LLM: chat_with_schema() → {valid: bool, reason: str|null} │
│  Output: (is_valid, reason)                                 │
│  If invalid: appends warning to response                    │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       ▼
┌─ Citation Extraction ─────────────────────────────────────┐
│  extract_all_citations() → list of "[Source: X, Slide Y]"  │
│  parse_citation() → (title, page_number)                   │
│  Match against retrieved chunks                            │
│  Output: [{source_title, page, content_type, has_image}]   │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       ▼
┌─ Metadata Yield ───────────────────────────────────────────┐
│  yields {"type": "metadata",                                │
│          "cited_sources": [...],                            │
│          "chunks_retrieved": N,                             │
│          "text_chunks": N, "image_chunks": N}              │
└────────────────────────────────────────────────────────────┘
```

For non-streaming path (`/query`): same flow but adds citation validation (`validate_citations`) and uncited claim removal (`remove_uncited_claims`) after verification step.

---

## 8. Docker Compose Connections

| Service | Depends On | Network | Port Mapping | Volumes |
|---------|-----------|---------|-------------|---------|
| surrealdb | — | default | 8000:8000 | `surreal_data:/data` |
| backend | surrealdb | default | 8001:8001 | `./backend/storage:/app/storage`, `./chroma_db:/app/chroma_db` |
| frontend | backend | default | 3000:3000 | — |
| postgres | — | default | 5433:5432 | `postgres_data:/var/lib/postgresql/data` |

**Notes:**
- Postgres is defined but NO code connects to it — dead service
- Backend connects to SurrealDB via `ws://surrealdb:8000/rpc` (Docker DNS)
- Frontend connects to Backend via `http://localhost:8001` (browser-side, not server-side)
- Volumes `surreal_data` and `postgres_data` are named Docker volumes

---

## 9. Frontend — Key File Connections

| File | Imports / Connects to | Purpose |
|------|----------------------|---------|
| layout.js | AppShell, Sidebar, TopBar, globals.css | Root layout wrapping all pages |
| page.js (Login) | FormField, Badge | Login form with role tabs → redirects to /dashboard, /faculty, or /admin |
| dashboard/page.js | StatTile, CourseCard, RadialProgress, MiniBarChart | Student dashboard with mock stats |
| chat/page.js | — | Empty placeholder ("coming soon") |
| courses/[code]/page.js | Dropzone, FileTypeIcon, Badge | Course detail with file upload and mock chat |
| progress/page.js | StatTile, ProgressBar, ActivityHeatmap | Learning progress with mock data |
| quiz/page.js | — | Empty placeholder ("under development") |
| flashcards/page.js | — | Empty placeholder ("under development") |
| faculty/page.js | StatTile, MiniBarChart, DataTable, ActivityHeatmap | Faculty dashboard with mock data |
| faculty/analytics/page.js | — | Empty placeholder ("coming soon") |
| faculty/generate/page.js | CheckboxCard, RemovableSection, BloomPill, PaperPreview | Question paper config + preview (mock) |
| faculty/course/[code]/page.js | Dropzone, FileTypeIcon, Badge | Upload materials with processing states |
| admin/page.js | StatTile, MiniBarChart, DataTable | Admin dashboard with user table |
| components/AppShell.js | Sidebar, TopBar | Layout orchestrator for all pages |
| components/Sidebar.js | lucide-react icons | Role-aware left navigation |
| components/TopBar.js | AvatarOrInitials, Breadcrumbs | 3 variants: search, tabs, breadcrumbBack |
| lib/mockData.js | — | All mock data exports (no imports needed) |
