# RAG Pipeline vs Open Notebook — Full Comparison & Improvement Plan

## Table of Contents
1. [Detailed System Comparison](#1-detailed-system-comparison)
2. [Open-Notebook Database Architecture](#2-open-notebook-database-architecture)
3. [Current System Architecture Analysis](#3-current-system-architecture-analysis)
4. [Complete Bug-Fix-Improvement List](#4-complete-bug-fix-improvement-list)
5. [Implementation Order (Dependency Graph)](#5-implementation-order-dependency-graph)
6. [Effort Estimate & Quick Wins](#6-effort-estimate--quick-wins)
7. [Appendices](#7-appendices)

---

## 1. Detailed System Comparison

### 1.1 Purpose & Scope

| Aspect | Current Implementation | Open-Notebook |
|--------|----------------------|---------------|
| **Primary Use** | CLI + API for course-based document QA | Full research-assistant web platform |
| **Target Users** | Students/courses (single-purpose) | Researchers, students, knowledge workers |
| **Deployment** | Single FastAPI server | Multi-service (API + commands + workers) |
| **Interface** | CLI + REST API | REST API + Web UI + Streaming |
| **Auth** | None | Password + encryption key |
| **Multi-tenancy** | No (single user) | Yes (notebook-based isolation) |

### 1.2 Technology Stack

| Layer | Current | Open-Notebook |
|-------|---------|---------------|
| **Database** | ChromaDB (vector-only) | SurrealDB (multi-model: document + vector + graph) |
| **Embedding** | OpenRouter (external) | Configurable provider (OpenAI, Ollama, etc.) |
| **LLM** | OpenRouter | Configurable provider via model manager |
| **Background Jobs** | None | surreal-commands system |
| **Search** | ChromaDB `.query()` | SurrealDB `fn::text_search()` + `fn::vector_search()` |
| **Chunking** | Sentence-based (plain text) | Content-aware (HTML/MD/plain with separate strategies) |
| **Token Counting** | Word splitting (`len(text.split())`) | tiktoken (`o200k_base` encoding) |
| **Logging** | `print()` statements | loguru |
| **Error Handling** | Try/except with print | Structured exception hierarchy + FastAPI handlers |
| **Evaluation** | Custom RAGAS-style | Test-based with `pytest` |

### 1.3 Database Comparison

| Feature | Current (ChromaDB) | Open-Notebook (SurrealDB) |
|---------|-------------------|--------------------------|
| **Storage Type** | Vector-only | Document + Vector + Graph |
| **Schema** | Metadata-only (flexible) | `SCHEMAFULL` with typed fields |
| **Relations** | None (flat metadata) | `reference`, `artifact` relation tables |
| **Full-text Search** | No | BM25 via `search::score()` |
| **Vector Search** | Cosine distance (built-in) | Cosine similarity via `vector::similarity::cosine()` |
| **Auto Timestamps** | Manual | `DEFAULT time::now()` |
| **Cascade Delete** | Manual (code) | SurrealDB events |
| **Migrations** | None (manual reset) | SurrealQL migration files (versioned) |
| **Queries** | `.query()` method | SurrealQL functions (`fn::text_search`, `fn::vector_search`) |
| **Connection** | Persistent client | Async connection pool |

### 1.4 RAG Pipeline Comparison

| Stage | Current | Open-Notebook |
|-------|---------|---------------|
| **Ingestion** | Inline (blocks request) | Background job (`embed_source` command) |
| **Chunking** | Sentence-based, 512 tokens | Content-aware (HTML/MD/plain), 400 tokens |
| **Chunk Overlap** | 64 tokens (hardcoded 3 sentences) | 15% (configurable via env) |
| **Embedding** | Single OpenRouter model | Configurable provider with batching + retries |
| **Long Text Handling** | Split into chunks | Auto-chunk + mean pooling |
| **Image Handling** | Separate ChromaDB collection | Content-type detection → same pipeline |
| **Search** | Vector only (cosine distance) | Text (BM25) + Vector (cosine) |
| **Context Building** | Hardcoded prompt template | `ContextBuilder` class with priorities + token limits |
| **LLM Query** | Single call with citation retry | Streaming + structured graphs |
| **Output** | Text with inline citations | Streamed strategy/answer/final pipeline |
| **Caching** | None | Not in core (command system enables it) |

---

## 2. Open-Notebook Database Architecture

### 2.1 Tables & Schema

```surrealql
-- Source: Main content items
DEFINE TABLE source SCHEMAFULL;
DEFINE FIELD asset      ON source TYPE option<object>;
DEFINE FIELD title      ON source TYPE option<string>;
DEFINE FIELD topics     ON source TYPE option<array<string>>;
DEFINE FIELD full_text  ON source TYPE option<string>;
DEFINE FIELD created    ON source DEFAULT time::now() VALUE $before OR time::now();
DEFINE FIELD updated    ON source DEFAULT time::now() VALUE time::now();

-- Source Embedding: Vector chunks linked to sources
DEFINE TABLE source_embedding SCHEMAFULL;
DEFINE FIELD source    ON source_embedding TYPE record<source>;
DEFINE FIELD order     ON source_embedding TYPE int;
DEFINE FIELD content   ON source_embedding TYPE string;
DEFINE FIELD embedding ON source_embedding TYPE array<float>;

-- Source Insight: AI-generated insights
DEFINE TABLE source_insight SCHEMAFULL;
DEFINE FIELD source        ON source_insight TYPE record<source>;
DEFINE FIELD insight_type  ON source_insight TYPE string;
DEFINE FIELD content       ON source_insight TYPE string;
DEFINE FIELD embedding     ON source_insight TYPE array<float>;

-- Note: User/AI notes
DEFINE TABLE note SCHEMAFULL;
DEFINE FIELD title     ON note TYPE option<string>;
DEFINE FIELD summary   ON note TYPE option<string>;
DEFINE FIELD content   ON note TYPE option<string>;
DEFINE FIELD embedding ON note TYPE array<float>;

-- Notebook: Organizational containers
DEFINE TABLE notebook SCHEMAFULL;
DEFINE FIELD name        ON notebook TYPE option<string>;
DEFINE FIELD description ON notebook TYPE option<string>;
DEFINE FIELD archived    ON notebook TYPE option<bool> DEFAULT False;

-- Relations
DEFINE TABLE reference TYPE RELATION FROM source TO notebook;
DEFINE TABLE artifact   TYPE RELATION FROM note TO notebook;
```

### 2.2 Search Functions

```surrealql
-- Full-Text Search (BM25)
DEFINE FUNCTION fn::text_search($query_text, $match_count, $sources, $show_notes) {
    -- Searches: source.title, source_embedding.content, source.full_text
    --           source_insight.content, note.title, note.content
    -- Combines via array::union()
    -- Returns (item_id, math::max(relevance)) ORDER BY relevance DESC LIMIT $match_count
};

-- Vector Search (Cosine Similarity)
DEFINE FUNCTION fn::vector_search($query, $match_count, $sources, $show_notes) {
    -- Uses vector::similarity::cosine(embedding, $query)
    -- Searches: source_embedding, source_insight, note
    -- Returns (item_id, math::max(similarity)) ORDER BY similarity DESC LIMIT $match_count
};
```

### 2.3 Repository Layer (Connection Management)

```python
@asynccontextmanager
async def db_connection():
    db = AsyncSurreal(get_database_url())
    await db.signin({"username": ..., "password": ...})
    await db.use(namespace, database)
    try:
        yield db
    finally:
        await db.close()
```

Repository functions: `repo_query()`, `repo_create()`, `repo_upsert()`, `repo_update()`, `repo_delete()`, `repo_insert()`, `repo_relate()`

### 2.4 Migration System

- Versioned SurrealQL files: `migrations/1.surrealql`, `migrations/1_down.surrealql`, etc.
- `AsyncMigrationManager` checks `_sbl_migrations` table for current version
- Runs pending migrations on API startup
- Supports up/down migrations

---

## 3. Current System Architecture Analysis

### 3.1 File Map

```
backend/
├── main.py                  # CLI entry point (ingest, query, eval, stats)
├── server.py                # FastAPI server (534 lines)
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── config.py            # Env-based settings (37 lines)
│   ├── db.py                # ChromaDB connection (39 lines)
│   ├── rag.py               # RAG pipeline (371 lines)
│   ├── openrouter.py        # OpenRouter client (262 lines)
│   ├── query_engine.py      # LLM query engine (247 lines)
│   ├── chunker.py           # Text chunking (71 lines)
│   ├── pdf_extractor.py     # PDF extraction (187 lines)
│   ├── citation.py          # Citation validation (96 lines)
│   ├── evaluator.py         # RAGAS evaluation (264 lines)
│   ├── curriculum.py        # Curriculum management
│   ├── analytics.py         # Query analytics
│   ├── chat_history.py      # Chat persistence
│   ├── courses.py           # Course CRUD
│   ├── paper_generator.py   # Paper generation
│   ├── saved_content.py     # Flashcard/quiz storage
│   ├── validation.py        # Input validation
│   └── ...
└── storage/                 # File-based storage for chats, quizzes, etc.
```

### 3.2 Data Flow

```
[PDF Upload] → pdf_extractor.py (text+images) → rag.ingest_pdf()
                                                      ├─ rag.ingest() → ChromaDB.text_chunks
                                                      └─ rag.ingest_images() → ChromaDB.image_chunks

[REST Query] → server.py /query → rag.retrieve() → ChromaDB (both collections)
                                                    └─ query_engine.query() → LLM (OpenRouter)
                                                                               └─ citation validation → response
```

### 3.3 Current Weaknesses Summary

| Category | Count | Key Issues |
|----------|-------|------------|
| **Bugs** | 5 | Fake token counting, except:pass, sentence splitting fragility |
| **Missing Features** | 10 | Background jobs, full-text search, content detection, insights, notes |
| **Design Issues** | 12 | No DB abstraction, O(n) scans, no retries, global instances |
| **Performance** | 4 | No connection pooling, no caching, new HTTP client per call |
| **Reliability** | 6 | No error middleware, print logging, no startup checks |

---

## 4. Complete Bug-Fix-Improvement List — All 8 Phases (41 Items)

---

### ▸ PHASE 0 — CRITICAL BUGS

**Goal**: Fix broken fundamentals that corrupt data and metrics.

**Dependency**: Nothing blocks this. Everything else depends on this.

**Effort**: ~2 hours | **Complexity**: Low

| # | Issue | File:Line | Current Problem | Fix | Impact |
|---|-------|-----------|-----------------|-----|--------|
| 1 | **Fake token counting** | `chunker.py:6` | Uses `len(text.split())` not real tokens | Replace with `tiktoken` or char/4 estimate | Chunk sizes are wrong, RAG metrics invalid |
| 2 | **No retry logic on OpenRouter** | `openrouter.py:36-96` | Single attempt fails immediately | Add 3 retries with 2s backoff | Random failures during embedding |
| 3 | **New HTTP client per call** | `openrouter.py:37,68,156,204` | Creates `httpx.AsyncClient()` fresh each call | Use shared client with connection pooling | 10-20% latency penalty |
| 4 | **`except: pass` masking errors** | `pdf_extractor.py:95-98,133-136` | Silent failures on image extraction | Log warnings, track failure counts | Images silently lost |
| 5 | **`remove_uncited_claims()` fragility** | `citation.py:33-49` | Splits on `. ` breaking URLs/decimals | Use regex or NLTK sentence splitting | Citation validation produces false positives |

**Blocking**: Phases 1, 2, 3, 4, 5, 6, 7

---

### ▸ PHASE 1 — CORE INFRASTRUCTURE

**Goal**: Lay foundation for all downstream improvements.

**Dependency**: Blocked by Phase 0.

**Effort**: ~8 hours | **Complexity**: Medium

| # | Issue | File:Line | Current Problem | Fix | Impact |
|---|-------|-----------|-----------------|-----|--------|
| 6 | **No background job system** | `server.py` | Inline processing blocks API response for large PDFs | Implement async job submission via command queue (`submit_command`) | Non-blocking ingestion, scalability |
| 7 | **No database abstraction layer** | `app/db.py` | Direct ChromaDB coupling throughout all modules | Create abstract Repository class with CRUD operations (`repo_query`, `repo_create`, `repo_update`, `repo_delete`) | Switch DB without rewriting everything |
| 8 | **No persistent relations** | N/A | Sources, notes, notebooks are flat metadata in ChromaDB | Add relation tables (`reference` source→notebook, `artifact` note→notebook) | Multi-source per course, notebooks |
| 9 | **No content-type detection** | `app/chunker.py` | Only plain text sentence-based splitting | Implement detection of HTML/Markdown/Plain via extension + heuristics | Appropriate chunking per file type |
| 10 | **No configurable chunk overlap** | `chunker.py:12` | Hardcoded overlap of 3 sentences | Configurable overlap percentage via `CHUNK_OVERLAP` env var | Finer control over chunk boundaries |

**Blocking**: Phases 2, 3, 6

---

### ▸ PHASE 2 — EMBEDDING PIPELINE

**Goal**: Robust, configurable embedding generation with retries and batching.

**Dependency**: Blocked by Phase 0, 1.

**Effort**: ~6 hours | **Complexity**: Medium

| # | Issue | File:Line | Current Problem | Fix | Impact |
|---|-------|-----------|-----------------|-----|--------|
| 11 | **No embedding batch size config** | `openrouter.py:67-96` | All texts sent in single API call | Add `EMBEDDING_BATCH_SIZE` env var (default 50) | Handle large documents without timeout |
| 12 | **No mean pooling for long texts** | `rag.py` | Can't handle texts exceeding token limit for single embedding | Implement `mean_pool_embeddings()`: normalize → mean → normalize | Embed any length text |
| 13 | **No auto-chunking during embedding** | `rag.py:31-49` | Text must be pre-chunked before calling ingest | Auto-detect long texts, chunk, embed each, mean-pool | Unified embedding API |
| 14 | **Image embedding stores only text description** | `rag.py:123-135` | ChromaDB gets text description, not actual image | Store image reference properly; use multimodal embedding API | True multimodal RAG |
| 15 | **No embedding model validation** | `rag.py:49` | Assumes embedding model always available | Add check at startup and before embedding (like Open Notebook's `embedding.py:138-142`) | Early failure instead of cryptic errors |

**Blocking**: Phases 3, 4

---

### ▸ PHASE 3 — DATABASE & SEARCH

**Goal**: Add full-text search, abstract vector search, proper statistics.

**Dependency**: Blocked by Phase 0, 1, 2.

**Effort**: ~16 hours | **Complexity**: High

| # | Issue | File:Line | Current Problem | Fix | Impact |
|---|-------|-----------|-----------------|-----|--------|
| 16 | **No full-text search** | `rag.py:225-298` | Only vector search available; zero results if embedding fails | Implement BM25 search via SurrealDB `fn::text_search`: search `title`, `full_text`, `source_embedding.content`, `source_insight.content`, `note.content` | Search works even without embeddings |
| 17 | **No vector search abstraction** | `rag.py:225-298` | `ChromaDB.query()` called inline everywhere | Create abstract `fn::vector_search`: cosine similarity against `embedding` fields, configurable `minimum_score` (0.2) | Consistent, testable search API |
| 18 | **O(n) full scans for statistics** | `rag.py:324-371` | `list_courses()` / `get_course_stats()` scan all records every time | Database-level aggregate queries (`SELECT count() GROUP BY course_code`) | Fast statistics even with millions of chunks |
| 19 | **No minimum score threshold** | `rag.py:225-298` | All results returned regardless of relevance | Add `minimum_score` parameter (default 0.2) with cosine threshold | Eliminates garbage results |
| 20 | **Only course_code filter** | `rag.py:237-239` | Metadata filtering by course_code only | Multi-dimensional filtering: topic + date + content_type + course_code | Precise retrieval scoping |

**Blocking**: Phase 4

---

### ▸ PHASE 4 — QUERY ENGINE & CONTEXT

**Goal**: Intelligent context assembly with prioritization, token limits, and hybrid search.

**Dependency**: Blocked by Phase 0, 2, 3.

**Effort**: ~8 hours | **Complexity**: Medium

| # | Issue | File:Line | Current Problem | Fix | Impact |
|---|-------|-----------|-----------------|-----|--------|
| 21 | **No ContextBuilder class** | `query_engine.py:54-106` | Hardcoded context assembly with fixed priority | Implement `ContextBuilder` with `ContextConfig`: priority weights (source=100, insight=75, note=50), dedup, formatted output | Flexible, reusable context assembly |
| 22 | **No token limit enforcement** | `query_engine.py:54-106` | Context window grows unbounded | Add `truncate_to_fit(max_tokens)`: pop lowest-priority items until under token budget | Never exceed LLM context window |
| 23 | **No hybrid search** | `rag.py:225-298` | Vector-only search; no BM25 fallback | Combine `fn::text_search` + `fn::vector_search` scores with weighted ranking | Best results from both search methods |
| 24 | **Hardcoded max_turns=8** | `query_engine.py:57` | Not configurable | Move to `MAX_CHAT_HISTORY_TURNS` env var | Configurable conversation memory |
| 25 | **No insight system** | N/A | No AI-generated insights on sources | Implement `SourceInsight` model: auto-generate summary/key points/explanation from `full_text`; store in `source_insight` table; include in context | Richer context for LLM |
| 26 | **Curriculum check short-circuits RAG** | `query_engine.py:147-155` | Returns "not in materials" before even checking RAG | Move curriculum check to AFTER RAG retrieval; use results to determine scope | RAG always consulted first |

**Blocking**: Phase 6

---

### ▸ PHASE 5 — API & SERVER

**Goal**: Production-ready API with caching, error handling, and security.

**Dependency**: Blocked by Phase 0, 1. Parallelizable with Phases 2, 3, 4.

**Effort**: ~4 hours | **Complexity**: Low

| # | Issue | File:Line | Current Problem | Fix | Impact |
|---|-------|-----------|-----------------|-----|--------|
| 27 | **No query caching** | `server.py:340-376` | Same question hits LLM every single time | Add 30-min TTL cache keyed on `(question, course_code, top_k)` | Reduces LLM costs, improves latency |
| 28 | **Global module-level instances** | `server.py:70-73` | `rag`, `engine`, `curriculum` at module scope; restart to reconfigure | Move to FastAPI `lifespan` or dependency injection | Proper lifecycle, testable |
| 29 | **No error handler middleware** | `server.py` | No structured error responses; exceptions may leak internals | Add FastAPI exception handlers for `NotFoundError`, `InvalidInputError`, `RateLimitError`, `ConfigurationError` etc. | Consistent error format, security |
| 30 | **Overly broad CORS (\*)** | `server.py:56-60` | Accepts requests from any origin | Configure via `CORS_ORIGINS` env var (comma-separated) with wildcard warning | Production security |
| 31 | **Upload size checked after full read** | `server.py:303-336` | Reads entire file into memory before checking size | Check `content-length` header first, reject early if > 15MB | Memory protection |

**Blocking**: Nothing (leaf phase)

---

### ▸ PHASE 6 — ADVANCED FEATURES

**Goal**: Full feature parity with modern RAG platforms.

**Dependency**: Blocked by all prior phases.

**Effort**: ~12 hours | **Complexity**: High

| # | Issue | File:Line | Current Problem | Fix | Impact |
|---|-------|-----------|-----------------|-----|--------|
| 32 | **No note system** | N/A | No user/AI notes per course | Implement `Note` model: title + content + embedding + human/ai type; auto-submit `embed_note` on save; searchable via `fn::text_search` | User knowledge capture |
| 33 | **No cascade delete** | `rag.py:314-322` | Deleting source leaves orphaned embeddings/insights | Add event-driven cleanup: `DELETE source_embedding WHERE source=$id` + file system cleanup | Data integrity |
| 34 | **No duplicate detection** | `rag.py:55-84` | Same document can be ingested multiple times | Add content hash (`SHA256 of full_text`) on source; reject or skip duplicates | Clean, deduplicated corpus |
| 35 | **No credential management** | N/A | All API keys in `.env`; no encryption | Implement credential service: encrypt secrets at rest using `OPEN_NOTEBOOK_ENCRYPTION_KEY`; store in SurrealDB | Security, rotation support |
| 36 | **No command/event queue** | N/A | No background processing infrastructure | Implement surreal-commands-like system: enqueue → worker picks up → processes → updates status | Async everything, full observability |
| 37 | **No ingestion progress tracking** | `rag.py:151-223` | User sees only final "done" result; no intermediate progress | Report per-chunk/step progress via command status API (similar to `Source.get_processing_progress()`) | User visibility for large docs |

**Blocking**: Nothing (leaf phase)

---

### ▸ PHASE 7 — MONITORING & RELIABILITY

**Goal**: Production observability, health checks, and safety.

**Dependency**: Incremental — can start alongside any phase.

**Effort**: ~3 hours | **Complexity**: Low

| # | Issue | File:Line | Current Problem | Fix | Impact |
|---|-------|-----------|-----------------|-----|--------|
| 38 | **No structured logging** | All files | `print()` statements everywhere; no log levels or routing | Replace with `loguru`; add `logger.info`, `logger.debug`, `logger.error`; configure log file + console | Searchable logs, production debugging |
| 39 | **No embedding timing metrics** | `rag.py, openrouter.py` | No visibility into embedding latency | Add lazy logging with min/max/total token metrics per batch (like `embedding.py:146-169`) | Performance optimization |
| 40 | **Minimal startup checks** | `server.py:45-49` | No validation on boot; fails at first request | Add checks on startup: encryption key exists, embedding model reachable, DB connection healthy | Fail fast, not at first request |
| 41 | **No database migrations** | `app/db.py` | Schema changes require manual ChromaDB reset and re-ingest | Implement versioned migration system (`_sbl_migrations` table, SurrealQL migration files, auto-run on startup) | Schema evolution without data loss |

**Blocking**: Nothing (leaf phase)

---

## 5. Dependency Graph — How Phases Connect

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DEPENDENCY FLOW                                    │
│                                                                              │
│  PHASE 0 ──→ PHASE 1 ──→ PHASE 2 ──→ PHASE 3 ──→ PHASE 4 ──→ PHASE 6      │
│  BUGS         INFRA        EMBED        DB+SEARCH    CONTEXT      ADVANCED  │
│  (5 items)    (5 items)    (5 items)    (5 items)    (6 items)    (6 items) │
│     │            │            │            │            │            │      │
│     │            │            │            │            │            │      │
│     └─────┬──────┘            │            └──────┬───────┘            │      │
│           │                   │                   │                    │      │
│           └───────────┬───────┘                   │                    │      │
│                       │                           │                    │      │
│                       └───────────────┬───────────┘                    │      │
│                                       │                                │      │
│                                       ▼                                │      │
│                                 PHASE 5                              │      │
│                                 API & SERVER  ────────────────────────┘      │
│                                 (5 items)                                     │
│                                       │                                      │
│                                       ▼                                      │
│                                 PHASE 7                                      │
│                                 MONITORING  (can start anytime)              │
│                                 (4 items)                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Detailed Dependency Rules

| Phase | Name | Items | Blocks | Blocked By | Can Run Parallel With |
|-------|------|-------|--------|------------|----------------------|
| **0** | Critical Bugs | 5 | Everything | Nothing | — (do first) |
| **1** | Core Infrastructure | 5 | 2, 3, 6 | 0 | Parts of 2 |
| **2** | Embedding Pipeline | 5 | 3, 4 | 0, 1 | Parts of 1 |
| **3** | Database & Search | 5 | 4 | 0, 1, 2 | Parts of 5 |
| **4** | Query Engine & Context | 6 | 6 | 0, 2, 3 | Parts of 5 |
| **5** | API & Server | 5 | Nothing | 0, 1 | 2, 3, 4 |
| **6** | Advanced Features | 6 | Nothing | All prior | None |
| **7** | Monitoring & Reliability | 4 | Nothing | Nothing (incremental) | All phases |

### Item-Level Dependency Chain

```
Phase 0          Phase 1          Phase 2          Phase 3          Phase 4          Phase 5          Phase 6          Phase 7
───────          ───────          ───────          ───────          ───────          ───────          ───────          ───────
                                                                                                                        
 #1 token_count  → #6 bg_jobs     → #11 batch_size  → #16 fulltext    → #21 context      → #27 cache        → #32 notes       → #38 logging
 #2 retry        → #7 db_abstraction → #12 mean_pool → #17 vec_search → #22 token_limit  → #28 di           → #33 cascade     → #39 metrics
 #3 http_client  → #8 relations   → #13 auto_chunk  → #18 stats      → #23 hybrid       → #29 error_handler → #34 dedup       → #40 startup
 #4 except:pass  → #9 content_type → #14 images     → #19 threshold  → #24 max_turns    → #30 cors         → #35 credentials → #41 migration
 #5 citation     → #10 overlap    → #15 validation   → #20 filters   → #25 insights     → #31 upload_size  → #36 commands
                                                                   → #26 curriculum                     → #37 progress
```

---

## 6. Effort Summary & Quick Wins

### Total Effort by Phase

| Phase | Items | Hours | Complexity | Priority |
|-------|-------|-------|------------|----------|
| **0 — Critical Bugs** | 5 | ~2 | Low | 🔴 MUST DO FIRST |
| **1 — Core Infrastructure** | 5 | ~8 | Medium | 🟡 FOUNDATION |
| **2 — Embedding Pipeline** | 5 | ~6 | Medium | 🟡 FOUNDATION |
| **3 — Database & Search** | 5 | ~16 | High | 🟠 HIGH IMPACT |
| **4 — Query Engine & Context** | 6 | ~8 | Medium | 🟠 HIGH IMPACT |
| **5 — API & Server** | 5 | ~4 | Low | 🟢 PRODUCTION |
| **6 — Advanced Features** | 6 | ~12 | High | 🟢 ENHANCEMENT |
| **7 — Monitoring & Reliability** | 4 | ~3 | Low | 🟢 OBSERVABILITY |
| **TOTAL** | **41** | **~59** | | |

### Quick Wins (Sorted by Impact/Hour)

| Rank | Item | Hours | Impact | Why |
|------|------|-------|--------|-----|
| ⭐⭐⭐ | #1 — Real token counting | 0.25 | **Critical** | Every chunk size, overlap, and metric depends on this |
| ⭐⭐⭐ | #3 — HTTP client reuse | 0.5 | **High** | 10-20% latency improvement, free |
| ⭐⭐⭐ | #19 — Minimum score threshold | 0.5 | **High** | Eliminates irrelevant results immediately |
| ⭐⭐ | #16 — Full-text search | 4.0 | **Very High** | Search works when embeddings fail |
| ⭐⭐ | #9 — Content-type detection | 1.0 | **High** | Correct chunking for HTML/MD vs plain text |
| ⭐⭐ | #29 — Error handlers | 1.0 | **High** | No more cryptic server errors |
| ⭐⭐ | #38 — Structured logging | 1.5 | **High** | Find bugs quickly in production |
| ⭐⭐ | #21 — ContextBuilder | 2.0 | **High** | Smart context, never exceed token limits |
| ⭐ | #2 — Retry logic | 1.0 | **Medium** | Reduces random failures |
| ⭐ | #12 — Mean pooling | 1.5 | **Medium** | Embed any text length |

### Suggested Sprints

| Sprint | Focus | Items | Hours | Goal |
|--------|-------|-------|-------|------|
| **Sprint 1** | Phase 0 + Phase 1 (#9, #10) | #1-5, #9-10 | ~4h | Fix bugs + content-aware chunking |
| **Sprint 2** | Phase 1 (#6-8) + Phase 2 | #6-8, #11-15 | ~8h | Background jobs + robust embeddings |
| **Sprint 3** | Phase 3 | #16-20 | ~8h | Full-text + vector search |
| **Sprint 4** | Phase 4 + Phase 5 (#27-29) | #21-26, #27-29 | ~8h | ContextBuilder + API hardening |
| **Sprint 5** | Phase 5 (#30-31) + Phase 7 | #30-31, #38-41 | ~4h | CORS, upload validation, monitoring |
| **Sprint 6** | Phase 6 | #32-37 | ~12h | Notes, insights, credentials, progress |
| **TOTAL** | | **41** | **~44h** (overlap savings) | Full RAG transformation |

---

## 7. Appendices

### A. Open-Notebook Embedding Utilities (Reference)

```python
# Key classes/functions from open_notebook/utils/embedding.py
async def generate_embedding(text, content_type=None, file_path=None, command_id=None):
    """Single text embedding with auto-chunking + mean pooling for long texts."""
    if token_count(text) <= CHUNK_SIZE:
        return await generate_embeddings([text])[0]
    chunks = chunk_text(text, content_type, file_path)
    embeddings = await generate_embeddings(chunks)
    return await mean_pool_embeddings(embeddings)

async def generate_embeddings(texts, command_id=None):
    """Batch embedding with retry logic."""
    for batch in batched(texts, EMBEDDING_BATCH_SIZE):
        for attempt in range(EMBEDDING_MAX_RETRIES):
            try:
                yield await model.aembed(batch)
                break
            except:
                await asyncio.sleep(EMBEDDING_RETRY_DELAY)

async def mean_pool_embeddings(embeddings):
    """Normalize → mean → normalize. Combines multiple chunk embeddings."""
    arr = np.array(embeddings)
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    normalized = arr / norms
    return (np.mean(normalized, axis=0) / np.linalg.norm(np.mean(normalized, axis=0))).tolist()
```

### B. Open-Notebook Database Repository (Reference)

```python
# Key functions from open_notebook/database/repository.py
async def repo_query(query_str, vars=None) -> List[Dict]:
    """Execute SurrealQL query with connection management."""

async def repo_create(table, data) -> Dict:
    """Create record with automatic created/updated timestamps."""

async def repo_update(table, id, data) -> List[Dict]:
    """Update record with updated=time::now()."""

async def repo_upsert(table, id, data, add_timestamp=False) -> List[Dict]:
    """UPSERT ... MERGE pattern for idempotent writes."""

async def repo_delete(record_id):
    """Delete record by ID."""

async def repo_relate(source, relationship, target, data=None):
    """RELATE source->relationship->target CONTENT data."""
```

### C. Open-Notebook Migration System (Reference)

```python
# From open_notebook/database/async_migrate.py
class AsyncMigrationManager:
    up_migrations = [AsyncMigration.from_file(f"open_notebook/database/migrations/{i}.surrealql")
                     for i in range(1, 16)]
    down_migrations = [AsyncMigration.from_file(f"open_notebook/database/migrations/{i}_down.surrealql")
                       for i in range(1, 16)]

    async def get_current_version(self) -> int:
        """Get max version from _sbl_migrations table."""

    async def needs_migration(self) -> bool:
        """Current version < len(up_migrations)."""

    async def run_migration_up(self):
        """Run all pending migrations in sequence."""
```

### D. Open-Notebook Domain Models (Reference)

```python
# From open_notebook/domain/notebook.py
class Source(ObjectModel):
    table_name = "source"
    asset: Optional[Asset]
    title: Optional[str]
    topics: Optional[List[str]]
    full_text: Optional[str]
    command: Optional[Union[str, RecordID]]

    async def vectorize(self) -> str:
        """Submit embed_source background command."""
        command_id = submit_command("open_notebook", "embed_source", {"source_id": str(self.id)})
        return command_id

    async def get_embedded_chunks(self) -> int:
        """SELECT count() as chunks FROM source_embedding WHERE source=$id"""

    async def get_insights(self) -> List[SourceInsight]:
        """SELECT * FROM source_insight WHERE source=$id"""

    async def add_insight(self, insight_type: str, content: str) -> Optional[str]:
        """Submit create_insight command (fire-and-forget)."""

    async def delete(self) -> bool:
        """Delete source + file + embeddings + insights."""

class Note(ObjectModel):
    table_name = "note"
    title: Optional[str]
    note_type: Optional[Literal["human", "ai"]]
    content: Optional[str]

    async def save(self) -> Optional[str]:
        """Save + submit embed_note command."""
        await super().save()
        return submit_command("open_notebook", "embed_note", {"note_id": str(self.id)})

class Notebook(ObjectModel):
    table_name = "notebook"
    name: str
    description: str
    archived: Optional[bool] = False

    async def get_sources(self) -> List[Source]: ...
    async def get_notes(self) -> List[Note]: ...
    async def get_chat_sessions(self) -> List[ChatSession]: ...
    async def get_delete_preview(self) -> Dict: ...
    async def delete(self, delete_exclusive_sources=False) -> Dict: ...

class SourceEmbedding(ObjectModel):
    table_name = "source_embedding"
    content: str

class SourceInsight(ObjectModel):
    table_name = "source_insight"
    insight_type: str
    content: str

    async def get_source(self) -> Source: ...
    async def save_as_note(self, notebook_id=None) -> Any: ...
```

### E. Open-Notebook Context Builder (Reference)

```python
# From open_notebook/utils/context_builder.py
@dataclass
class ContextConfig:
    sources: Dict[str, str]          # {source_id: inclusion_level}
    notes: Dict[str, str]            # {note_id: inclusion_level}
    include_insights: bool = True
    include_notes: bool = True
    max_tokens: Optional[int] = None
    priority_weights: Dict[str, int] = {"source": 100, "note": 50, "insight": 75}

class ContextBuilder:
    def __init__(self, **kwargs):
        self.source_id = kwargs.get("source_id")
        self.notebook_id = kwargs.get("notebook_id")
        self.include_insights = kwargs.get("include_insights", True)
        self.include_notes = kwargs.get("include_notes", True)
        self.max_tokens = kwargs.get("max_tokens")
        self.context_config = kwargs.get("context_config") or ContextConfig()

    async def build(self) -> Dict:
        """Build context from sources, notes, insights with priority + token management."""
        if self.source_id:     await self._add_source_context(self.source_id)
        if self.notebook_id:   await self._add_notebook_context(self.notebook_id)
        self.remove_duplicates()
        self.prioritize()
        if self.max_tokens:    self.truncate_to_fit(self.max_tokens)
        return self._format_response()
```

### F. Current Code: All Python Files Reference

```python
# backend/app/db.py — ChromaDB connection (39 lines)
# backend/app/config.py — Environment settings (37 lines)
# backend/app/rag.py — RAG pipeline (371 lines)
# backend/app/openrouter.py — OpenRouter client (262 lines)
# backend/app/query_engine.py — LLM query engine (247 lines)
# backend/app/citation.py — Citation validation (96 lines)
# backend/app/chunker.py — Text chunking (71 lines)
# backend/app/pdf_extractor.py — PDF extraction (187 lines)
# backend/app/evaluator.py — RAGAS evaluation (264 lines)
# backend/server.py — FastAPI server (534 lines)
```
