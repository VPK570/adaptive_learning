# Adaptive Learning Platform — Full Implementation Reference

> **Generated:** 2026-07-28  
> **MVP Readiness:** 3/10 — functional core, significant technical debt.  
> **Stack:** FastAPI + SurrealDB + Next.js 16 + Gemini/OpenRouter LLM

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Directory Structure](#3-directory-structure)
4. [Backend Implementation](#4-backend-implementation)
   - 4.1 [server.py — Entrypoint & Middleware](#41-serverpy--entrypoint--middleware)
   - 4.2 [Configuration (config.py)](#42-configuration-configpy)
   - 4.3 [Database Layer (db.py)](#43-database-layer-dbpy)
   - 4.4 [Provider Router (provider_router.py)](#44-provider-router-provider_routerpy)
   - 4.5 [RAG Pipeline (rag.py)](#45-rag-pipeline-ragpy)
   - 4.6 [Query Engine (query_engine.py)](#46-query-engine-query_enginepy)
   - 4.7 [Authentication (auth.py)](#47-authentication-authpy)
   - 4.8 [Validation (validation.py)](#48-validation-validationpy)
   - 4.9 [Gatekeeper (gatekeeper.py)](#49-gatekeeper-gatekeeperpy)
   - 4.10 [Verifier (verifier.py)](#410-verifier-verifierpy)
   - 4.11 [Chunker (chunker.py)](#411-chunker-chunkerpy)
   - 4.12 [Citation Enforcement (citation.py)](#412-citation-enforcement-citationpy)
   - 4.13 [Knowledge State (knowledge_state.py)](#413-knowledge-state-knowledge_statepy)
   - 4.14 [Curriculum Manager (curriculum.py)](#414-curriculum-manager-curriculumpy)
   - 4.15 [Topic Extraction (topics.py)](#415-topic-extraction-topicspy)
   - 4.16 [Learning Path (learning_path.py)](#416-learning-path-learning_pathpy)
   - 4.17 [Analytics (analytics.py)](#417-analytics-analyticspy)
   - 4.18 [PDF Extractor (pdf_extractor.py)](#418-pdf-extractor-pdf_extractropy)
   - 4.19 [Query Enhancer (query_enhancer.py)](#419-query-enhancer-query_enhancerpy)
   - 4.20 [Paper Generator (paper_generator.py)](#420-paper-generator-paper_generatorpy)
   - 4.21 [Bloom Classifier (bloom_classifier.py)](#421-bloom-classifier-bloom_classifierpy)
   - 4.22 [Gap Detection (gap_detection.py)](#422-gap-detection-gap_detectionpy)
   - 4.23 [Evaluator (evaluator.py)](#423-evaluator-evaluatorpy)
   - 4.24 [Scheduler (scheduler.py)](#424-scheduler-schedulerpy)
   - 4.25 [Knowledge Tracing (knowledge_tracing.py)](#425-knowledge-tracing-knowledge_tracingpy)
   - 4.26 [Deep KT (deep_kt.py)](#426-deep-kt-deep_ktpy)
   - 4.27 [Chat History (chat_history.py)](#427-chat-history-chat_historypy)
   - 4.28 [Courses (courses.py)](#428-courses-coursespy)
    - 4.29 [Celery Tasks (tasks.py)](#429-celery-tasks-taskspy)
    - 4.30 [Redis Client (redis_client.py)](#430-redis-client-redis_clientpy)
    - 4.31 [Dependencies (deps.py)](#431-dependencies-depspy)
    - 4.32 [Logging Middleware (logging_middleware.py)](#432-logging-middleware-logging_middlewarepy)
    - 4.33 [Schemas (schemas.py)](#433-schemas-schemaspy)
    - 4.34 [Router: auth.py](#434-router-authpy)
    - 4.35 [Router: query.py](#435-router-querypy)
    - 4.36 [Router: courses.py](#436-router-coursespy)
    - 4.37 [Router: ingestion.py](#437-router-ingestionpy)
    - 4.38 [Router: chat.py](#438-router-chatpy)
    - 4.39 [Router: flashcards.py](#439-router-flashcardspy)
    - 4.40 [Router: quiz.py](#440-router-quizpy)
    - 4.41 [Router: analytics.py](#441-router-analyticspy)
    - 4.42 [Router: paper.py](#442-router-paperpy)
    - 4.43 [Router: images.py](#443-router-imagespy)
    - 4.44 [Router: admin.py](#444-router-adminpy)
    - 4.45 [Router: users.py](#445-router-userspy)
    - 4.46 [Router: learning_path.py](#446-router-learning_pathpy)
    - 4.47 [Router: tasks.py](#447-router-taskspy)
5. [Database Schema](#5-database-schema)
6. [Frontend Implementation](#6-frontend-implementation)
   - 6.1 [Package Dependencies](#61-package-dependencies)
   - 6.2 [Next.js Configuration](#62-nextjs-configuration)
   - 6.3 [TypeScript Configuration](#63-typescript-configuration)
   - 6.4 [API Client Layer](#64-api-client-layer)
   - 6.5 [Auth Store](#65-auth-store)
   - 6.6 [Pages & Layouts](#66-pages--layouts)
   - 6.7 [Components](#67-components)
   - 6.8 [API Modules](#68-api-modules)
   - 6.9 [CSS Architecture](#69-css-architecture)
7. [Infrastructure](#7-infrastructure)
   - 7.1 [Docker Compose](#71-docker-compose)
   - 7.2 [Backend Dockerfile](#72-backend-dockerfile)
   - 7.3 [Frontend Dockerfile](#73-frontend-dockerfile)
   - 7.4 [Production Deployment (prod.sh)](#74-production-deployment-prodsh)
8. [Testing](#8-testing)
   - 8.1 [Python Tests](#81-python-tests)
   - 8.2 [Playwright E2E Tests](#82-playwright-e2e-tests)
9. [Configuration Reference](#9-configuration-reference)
10. [RAG Pipeline Data Flow](#10-rag-pipeline-data-flow)
11. [Known Technical Debt](#11-known-technical-debt)
12. [Status & Deferred Items](#12-status--deferred-items)

---

## 1. Project Overview

The **Adaptive Learning Platform** is a multimodal RAG (Retrieval-Augmented Generation) adaptive learning system designed for VIT Vellore students. It ingests PDF course materials (text + diagrams), indexes them via vector embeddings, and provides Socratic tutoring through an LLM-powered Q&A interface with citation-grounded answers.

### Core Capabilities
- **PDF Ingestion** — extract text and images from PDFs, chunk, embed, index
- **Hybrid Search** — BM25 full-text + vector cosine similarity with RRF fusion
- **Socratic Tutoring** — LLM generates answers with inline citations from course materials
- **Role-Based Access** — student, faculty, admin roles with distinct dashboards
- **Assessment Generation** — quizzes, flashcards, exam papers with Bloom's taxonomy levels
- **Knowledge Tracing** — Bayesian Knowledge Tracking per (topic × Bloom level)
- **Learning Paths** — prerequisite DAG with Zone of Proximal Development recommendations
- **Analytics** — topic coverage, weak topic detection, question frequency, Bloom's mastery

### LLM Architecture
| Traffic | Provider | Model(s) |
|---------|----------|----------|
| Chat completions | Google Gemini (multi-key) | `gemma-4-31b-it`, `gemini-3.6-flash` |
| Structured output | Gemini | Same models with `response_format: json_object` |
| Text embeddings | OpenRouter (multi-key) | `nvidia/llama-nemotron-embed-vl-1b-v2:free` |
| Image embeddings | OpenRouter | Same (multimodal mode, 1024-dim) |

### Infrastructure
- **Database:** SurrealDB (document DB with HNSW vector indexes), file-persisted via Docker
- **Queue:** Redis + Celery for background ingestion
- **Frontend:** Next.js 16 App Router, plain CSS, no Tailwind
- **API Proxy:** Next.js rewrites (28 rules) — no CORS between frontend and backend

---

## 2. System Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          FRONTEND (:3000)                                │
│  Next.js 16 App Router · React 19 · CSS Modules · Zustand · Axios       │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │  /login  /register  /student/*  /faculty/*  /admin/*               │  │
│  │  AppShell → Sidebar + TopBar + Content                             │  │
│  │  SSE streaming for AI chat (direct + Celery async)                   │  │
│  └──────────────────────┬─────────────────────────────────────────────┘  │
│                          │ 28 Next.js rewrites (no CORS)                 │
│                          ▼                                                │
│  ┌──────────────────────────────────────────────────────────────────────┐│
│  │                      BACKEND (:8001)                                 ││
│  │  FastAPI · SurrealDB · Celery · Gemini + OpenRouter                 ││
│  │                                                                      ││
│  │  Middleware Stack:                                                   ││
│  │    CORSMiddleware → SlowAPIMiddleware → upload_size →                ││
│  │    request_id → auth_middleware                                     ││
│  │                                                                      ││
│  │  server.py (lifespan → init DB + default users + services)          ││
│  │    ├── 14 routers mounted                                            ││
│  │    ├── rag.py (RAGPipeline)                                          ││
│  │    ├── query_engine.py (QueryEngine)                                 ││
│  │    ├── curriculum.py (CurriculumManager)                             ││
│  │    ├── knowledge_state.py (KnowledgeStateManager)                    ││
│  │    ├── provider_router.py (ProviderRouter — multi-key routing)       ││
│  │    └── tasks.py (Celery worker)                                      ││
│  └────────────────┬─────────────────────────────────────────────────────┘│
│                   │                                                       │
│          ┌────────┴────────┐                   ┌──────────────────┐      │
│          │   SurrealDB     │                   │    External       │      │
│          │   (:8000)       │                   │    Providers      │      │
│          │   File-based    │                   │                   │      │
│          │   Document DB   │                   │  Google Gemini    │      │
│          │   HNSW Vector   │                   │  (chat completions)│      │
│          │   14 tables     │                   │  OpenRouter       │      │
│          │                 │                   │  (embeddings)     │      │
│          └─────────────────┘                   └──────────────────┘      │
└──────────────────────────────────────────────────────────────────────────┘

                          Services (Docker Compose):
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ surrealdb│  │  redis   │  │ backend  │  │  worker  │  │ frontend │
│ :8000    │  │ :6379    │  │ :8001    │  │ (Celery) │  │ :3000    │
└──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘
```

### Service Dependency Graph

```
surrealdb ──→ backend ──→ frontend
redis ──────→ worker
surrealdb ──→ worker
```

### Data Flow (Query Request)

**Direct SSE path:**
```
User → Frontend → Next.js Rewrite → Backend /query-stream
  → Gatekeeper (LLM relevance check)
  → Query Enhancer (LLM generates 3 search queries)
  → RAGPipeline.retrieve (embed query → HNSW vector search + BM25 → RRF fusion)
  → build_tutor_prompt (system prompt + context window + history + query)
  → LLM chat completion (Gemini, streaming)
  → Verifier (LLM checks grounding in retrieved chunks)
  → Citation extraction (regex match to source chunks)
  → Persist query_log + chat_history
  → SSE response to frontend
```

**Async Celery path (decouples LLM from HTTP lifecycle):**
```
User → Frontend → POST /query-async (FastAPI)
  → Celery task process_query_task.delay()
  → Celery runs full pipeline (gatekeeper → enhancer → retrieve → LLM → verifier → extract)
  → Each SSE chunk RPUSHed to Redis list query_progress:{task_id}
  → Frontend GET /query-stream/{task_id} polls Redis via LRANGE
  → SSE terminates on {"type": "done"} or {"type": "error"}
  → Celery persists query_log + chat_history on completion
  → Redis key auto-expires after 600s
```

> **LaTeX TikZ — System Architecture Diagram:**
> ```latex
> \documentclass[tikz,border=10pt]{standalone}
> \usepackage{tikz}
> \usetikzlibrary{positioning,arrows.meta,shapes.geometric,fit,backgrounds}
> \begin{document}
> \begin{tikzpicture}[
>   node distance=1.5cm and 2.5cm,
>   box/.style={rectangle, draw, rounded corners, minimum width=3cm, minimum height=1.2cm, align=center, font=\sffamily},
>   db/.style={cylinder, draw, shape border rotate=90, minimum width=2.5cm, minimum height=1.5cm, aspect=0.3, align=center, font=\sffamily},
>   worker/.style={box, fill=yellow!10},
>   service/.style={box, fill=blue!10},
>   front/.style={box, fill=green!10},
>   ext/.style={box, fill=red!10, dashed},
>   arrow/.style={-{Latex[length=2mm]}, thick}
> ]
> \node[font=\Large\bfseries\sffamily] at (0,6.5) {Adaptive Learning Platform --- System Architecture};
> \node[ext] (gemini) at (-6,4.5) {Google Gemini\\Chat Completions};
> \node[ext] (openrouter) at (-6,2) {OpenRouter\\Embeddings};
> \node[db] (surrealdb) at (-1.5,-1) {SurrealDB\\:8000};
> \node[service] (redis) at (3,-1) {Redis\\:6379};
> \node[service] (backend) at (-1.5,1.5) {Backend\\FastAPI :8001};
> \node[worker] (worker) at (3,1.5) {Worker\\Celery};
> \node[front] (frontend) at (-1.5,4.5) {Frontend\\Next.js :3000};
> \draw[arrow] (frontend) -- node[right,font=\small\sffamily] {28 rewrites} (backend);
> \draw[arrow] (backend) -- node[left,font=\small\sffamily] {WS RPC} (surrealdb);
> \draw[arrow] (backend) -- node[above,font=\small\sffamily] {Redis} (redis);
> \draw[arrow] (worker) -- (redis);
> \draw[arrow,dashed] (worker) -- node[below left,font=\small\sffamily] {SurrealQL} (surrealdb);
> \draw[arrow] (backend) -- (gemini);
> \draw[arrow] (backend) -- (openrouter);
> \draw[arrow] (worker) -- (gemini);
> \draw[arrow] (worker) -- (openrouter);
> \begin{scope}[on background layer]
> \node[rectangle, draw, dotted, rounded corners, fill=gray!3, fit={(surrealdb)(redis)(backend)(worker)}, label={[font=\small\sffamily]above:Docker (5 services)}] {};
> \end{scope}
> \end{tikzpicture}
> \end{document}
> ```

> **LaTeX TikZ — Async Query Flow (Sequence Diagram):**
> ```latex
> \documentclass[tikz,border=10pt]{standalone}
> \usepackage{tikz}
> \usetikzlibrary{positioning,arrows.meta}
> \begin{document}
> \begin{tikzpicture}[
>   actor/.style={rectangle, draw, minimum width=2.2cm, minimum height=0.8cm, align=center, font=\small\bfseries\sffamily},
>   arrow/.style={-{Latex[length=2mm]}, thick},
>   msg/.style={font=\footnotesize\sffamily, align=center, fill=white, inner sep=2pt}
> ]
> \node[font=\Large\bfseries\sffamily] at (0,7.5) {Async Query --- 3-Tier Pipeline};
> \node[actor] (browser) at (-5,5.5) {Browser};
> \node[actor] (nextjs) at (-2,5.5) {Next.js};
> \node[actor] (fastapi) at (1,5.5) {FastAPI};
> \node[actor] (celery) at (4,5.5) {Celery};
> \node[actor] (redis) at (7,5.5) {Redis};
> \node[actor] (gemini) at (10,5.5) {Gemini};
> \foreach \x/\name in {-5/browser,-2/nextjs,1/fastapi,4/celery,7/redis,10/gemini} {
>   \draw[thick] (\x,5) -- (\x,-1);
> }
> \draw[arrow] (-5,4.5) -- node[above,msg] {POST /query-async} (-2,4.5);
> \draw[arrow] (-2,4.2) -- node[above,msg] {proxy} (1,4.2);
> \draw[arrow] (1,3.9) -- node[above,msg] {process\_query\_task.delay()} (4,3.9);
> \draw[arrow] (4,3.6) -- node[above,msg] {task\_id} (1,3.6);
> \draw[arrow] (1,3.3) -- node[above,msg] {task\_id} (-2,3.3);
> \draw[arrow] (-2,3.0) -- node[above,msg] {task\_id} (-5,3.0);
> \draw[arrow] (-5,2.2) -- node[above,msg] {GET /query-stream/\{task\_id\}} (-2,2.2);
> \draw[arrow] (-2,1.9) -- node[above,msg] {proxy} (1,1.9);
> \draw[arrow] (1,1.6) -- node[above,msg] {LRANGE} (7,1.6);
> \draw[arrow] (7,1.3) -- node[above,msg] {SSE chunks} (1,1.3);
> \draw[arrow] (1,1.0) -- node[above,msg] {data: \{...\}} (-2,1.0);
> \draw[arrow] (-2,0.7) -- node[above,msg] {SSE stream} (-5,0.7);
> \draw[arrow] (4,3.9) -- node[above,msg] {query\_stream()} (10,3.9);
> \draw[arrow] (10,3.6) -- node[above,msg] {SSE chunks} (4,3.6);
> \draw[arrow] (4,3.3) -- node[above,msg] {RPUSH} (7,3.3);
> \draw[arrow] (4,0) -- node[above,msg] {RPUSH done + EXPIRE 600s} (7,0);
> \draw[arrow] (7,-0.3) -- node[above,msg] {type:done} (1,-0.3);
> \draw[arrow] (1,-0.6) -- (2,-0.6);
> \node at (3.5,-0.6) [font=\footnotesize\sffamily] {Connection closes};
> \end{tikzpicture}
> \end{document}
> ```

---

## 3. Directory Structure

```
dont touch/
├── .env                          # Secrets & config (git-ignored)
├── .env.example                  # Template for .env
├── .gitignore
├── AGENTS.md                     # Agent guide for AI coding tools
├── IMPLEMENTATION.md             # ← This file
├── README.md                     # Project README
├── docker-compose.yml            # 5-service Docker Compose
├── prod.sh                       # Production deployment script
├── seed.spec.ts                  # Playwright test seed stub
│
├── backend/
│   ├── .env                      # Backend-specific env vars
│   ├── .dockerignore
│   ├── Dockerfile                # Python 3.11-slim multi-stage
│   ├── requirements.txt          # 20 Python dependencies
│   ├── ruff.toml                 # Ruff config (line-length=120, py311)
│   ├── server.py                 # FastAPI entrypoint
│   ├── lect1.md                  # Sample lecture notes (BACSE101)
│   ├── storage/                  # Uploaded files
│   ├── scripts/
│   │   └── eval_pipeline.py      # CLI RAG evaluation script
│   ├── tests/
│   │   ├── conftest.py           # Pytest fixtures (SurrealDB cleanup)
│   │   ├── test_auth.py          # 17 tests: hashing, JWT, roles
│   │   ├── test_db_logic.py      # DB CRUD, schema, analytics
│   │   ├── test_rag.py           # Chunking, citation, pipeline
│   │   ├── test_e2e_pipeline.py  # E2E integration (skipped by default)
│   │   ├── test_api_limits.py    # Upload size, rate limits
│   │   ├── test_validation.py    # Input sanitization
│   │   ├── test_validation_extended.py  # Injection patterns
│   │   └── test_scheduler.py     # Spaced repetition math
│   └── app/
│       ├── __init__.py
│       ├── server.py             # (not used — server.py is at root)
│       ├── config.py             # Settings class (~50 env vars)
│       ├── db.py                 # SurrealDBManager singleton
│       ├── auth.py               # JWT + bcrypt + RBAC
│       ├── rag.py                # RAGPipeline (ingest, retrieve, stats)
│       ├── redis_client.py       # Redis singleton for Celery streaming
│       ├── query_engine.py       # QueryEngine (prompt building, streaming)
│       ├── provider_router.py    # Multi-key LLM router (Gemini + OpenRouter)
│       ├── openrouter.py         # Legacy OpenRouter-only client
│       ├── gatekeeper.py         # LLM relevance filter
│       ├── verifier.py           # LLM grounding verifier
│       ├── chunker.py            # Sentence-aware tiktoken chunking
│       ├── citation.py           # Citation regex + validation
│       ├── knowledge_state.py    # BKT mastery model
│       ├── curriculum.py         # Curriculum PDF ingestion
│       ├── topics.py             # LLM topic extraction from syllabus
│       ├── learning_path.py      # Prerequisite DAG + ZPD candidates
│       ├── analytics.py          # Query logging, coverage, insights
│       ├── pdf_extractor.py      # PyPDF text + image extraction
│       ├── query_enhancer.py     # LLM multi-query generation
│       ├── paper_generator.py    # Exam paper generation
│       ├── bloom_classifier.py   # Bloom's level classification
│       ├── gap_detection.py      # Cognitive gap detection
│       ├── evaluator.py          # RAGAS-style evaluation metrics
│       ├── scheduler.py          # Spaced repetition scheduler
│       ├── knowledge_tracing.py  # BKT model implementation
│       ├── deep_kt.py            # DKT LSTM skeleton (dormant)
│       ├── chat_history.py       # Chat message persistence
│       ├── courses.py            # Course CRUD operations
│       ├── tasks.py              # Celery worker definition
│       ├── deps.py               # FastAPI dependency injection
│       ├── schemas.py            # Pydantic request/response models
│       ├── validation.py         # Input sanitization + injection detection
│       └── logging_middleware.py # ContextVar request ID
│       └── routers/
│           ├── __init__.py
│           ├── auth.py           # POST /auth/login, /auth/register
│           ├── query.py          # GET /health, POST /query, /query-stream, etc.
│           ├── courses.py        # CRUD /courses
│           ├── ingestion.py      # POST /ingest, /curriculum, DELETE /materials
│           ├── chat.py           # CRUD /chat-history
│           ├── flashcards.py     # POST /flashcards, save/list/delete
│           ├── quiz.py           # POST /quiz, save/list/delete
│           ├── analytics.py      # GET /analytics/*, /questions
│           ├── paper.py          # POST /generate-paper
│           ├── images.py         # POST /chat-images, GET /chat-images/*
│           ├── admin.py          # GET /admin/users, /admin/stats
│           ├── users.py          # GET/PUT /users/me
│           ├── learning_path.py  # GET /api/learning-path/*
│           └── tasks.py          # GET/DELETE /tasks/{id}, POST /scheduler/run
│
└── new_frontend/
    ├── .dockerignore
    ├── .gitignore
    ├── AGENTS.md                 # Next.js 16 breaking-changes warning
    ├── CLAUDE.md                 # @AGENTS.md include directive
    ├── Dockerfile                # Node 20 multi-stage (standalone output)
    ├── next.config.mjs           # 26 rewrite rules, standalone output
    ├── tsconfig.json             # strict: false, ES2017 target
    ├── eslint.config.mjs         # next/core-web-vitals flat config
    ├── package.json              # 10 deps, 7 devDeps
    ├── playwright.config.ts      # 6 projects, 3 auth states
    ├── next-env.d.ts
    ├── public/
    ├── e2e/                      # Playwright spec files
    │   ├── global-setup.ts       # Registers 3 users, saves auth state
    │   ├── auth.setup.ts
    │   ├── auth.spec.ts
    │   ├── student.spec.ts
    │   ├── faculty.spec.ts
    │   └── admin.spec.ts
    └── src/
        ├── app/
        │   ├── favicon.ico
        │   ├── globals.css        # Design tokens, CSS custom properties
        │   ├── layout.tsx         # Root layout (Inter + JetBrains Mono)
        │   ├── providers.tsx      # React Query + Toast providers
        │   ├── page.tsx           # Login page
        │   ├── register/page.tsx  # Registration page
        │   ├── components/
        │   │   ├── AppShell.tsx + .css
        │   │   ├── AvatarOrInitials.tsx + .css
        │   │   ├── Badge.tsx + .css
        │   │   ├── BloomPill.tsx + .css
        │   │   ├── Breadcrumbs.tsx + .css
        │   │   ├── CheckboxCard.tsx + .css
        │   │   ├── CourseCard.tsx + .css
        │   │   ├── DataTable.tsx + .css
        │   │   ├── Dropzone.tsx + .css
        │   │   ├── FileTypeIcon.tsx + .css
        │   │   ├── FormField.tsx + .css
        │   │   ├── Modal.tsx + .css
        │   │   ├── PaperPreview.tsx + .css
        │   │   ├── ProgressBar.tsx + .css
        │   │   ├── RadialProgress.tsx + .css
        │   │   ├── RemovableSection.tsx + .css
        │   │   ├── Sidebar.tsx + .css
        │   │   ├── StatTile.tsx + .css
        │   │   ├── Toast.tsx + .css
        │   │   ├── ToastContext.tsx
        │   │   └── TopBar.tsx + .css
        │   ├── admin/
        │   │   ├── layout.tsx        # Auth guard: admin only
        │   │   ├── dashboard/page.tsx + .css
        │   │   └── profile/page.tsx
        │   ├── faculty/
        │   │   ├── layout.tsx        # Auth guard: faculty only
        │   │   ├── dashboard/page.tsx + .css (+ AddCourseModal.tsx)
        │   │   ├── analytics/page.tsx + .css
        │   │   ├── course/[code]/page.tsx + .css
        │   │   ├── generate/page.tsx + .css
        │   │   └── profile/page.tsx
        │   └── student/
        │       ├── layout.tsx        # Auth guard: student only
        │       ├── dashboard/page.tsx + .css
        │       ├── courses/[code]/page.tsx + .css
        │       ├── quiz/page.tsx + .css
        │       ├── flashcards/page.tsx + .css
        │       ├── progress/page.tsx + .css
        │       └── profile/page.tsx
        └── lib/
            ├── api/
            │   ├── client.ts         # Axios instance (Bearer interceptor)
            │   ├── types.ts          # 30+ TypeScript interfaces
            │   ├── auth.ts
            │   ├── courses.ts
            │   ├── chat.ts
            │   ├── flashcards.ts
            │   ├── quiz.ts
            │   ├── paper.ts
            │   ├── ingestion.ts
            │   ├── admin.ts
            │   ├── analytics.ts
            │   └── users.ts
            └── store/
                └── authStore.ts      # Zustand + localStorage (key: uniauth)
```

---

## 4. Backend Implementation

### 4.1 server.py — Entrypoint & Middleware

**File:** `backend/server.py` (163 lines)

The FastAPI application entrypoint. It configures logging, mounts middleware, initializes services on startup, and includes 14 routers.

#### Logging Setup (lines 20-34)

Uses `ContextVar` for per-request IDs. Custom `LogRecordFactory` injects `request_id` into every log record. Format: `%(asctime)s | %(levelname)-8s | %(request_id)s | %(name)s | %(message)s`.

```python
# Custom factory to inject request_id into every log record
def _make_record(*args, **kwargs):
    r = _old_factory(*args, **kwargs)
    r.request_id = request_id_var.get()[:8] or "-"
    return r
logging.setLogRecordFactory(_make_record)
```

#### Lifespan (lines 49-72)

Async context manager that runs on startup/shutdown:
1. Calls `SurrealDBManager.get_db()` — establishes SurrealDB connection + schema init
2. Creates 3 default users if they don't exist: `student@test.com`, `faculty@test.com`, `admin@test.com` — all password `password123`
3. Instantiates 4 global services on `app.state`:
   - `app.state.rag` = `RAGPipeline()`
   - `app.state.engine` = `QueryEngine()`
   - `app.state.curriculum` = `CurriculumManager()`
   - `app.state.knowledge_state` = `KnowledgeStateManager()`
4. Runs `yield` — app serves requests
5. On shutdown: logs "Shutting down..." (no explicit cleanup)

#### Middleware Stack (in order)

| Middleware | Lines | Purpose |
|-----------|-------|---------|
| `SlowAPIMiddleware` | 80 | Rate limiting: 60 req/min per IP |
| `CORSMiddleware` | 82-88 | CORS from `settings.CORS_ORIGINS` |
| `limit_upload_size` | 102-108 | Rejects POST/PUT > 15MB with 413 |
| `request_id_middleware` | 114-123 | Sets `X-Request-ID` or generates UUID, propagates via `ContextVar` |
| `auth_middleware` | 125-142 | JWT validation on all non-public routes |

#### Auth Middleware (lines 125-142)

Public routes (no JWT required):
- `/auth`, `/health`, `/docs`, `/openapi.json`, `/redoc`
- `GET /chat-images/*` (public image serving)
- `OPTIONS` (preflight)

For all other routes:
1. Checks `Authorization: Bearer <token>` header
2. Decodes JWT via `decode_token()`
3. Sets `request.state.user = {"email": ..., "role": ...}`
4. On failure: returns 401

#### Routers Mounted (lines 145-158)

| Router | Prefix | File |
|--------|--------|------|
| `query.router` | — | `routers/query.py` |
| `courses.router` | — | `routers/courses.py` |
| `chat.router` | — | `routers/chat.py` |
| `ingestion.router` | — | `routers/ingestion.py` |
| `flashcards.router` | — | `routers/flashcards.py` |
| `quiz.router` | — | `routers/quiz.py` |
| `paper.router` | — | `routers/paper.py` |
| `images.router` | — | `routers/images.py` |
| `auth_routes.router` | — | `routers/auth.py` |
| `analytics.router` | — | `routers/analytics.py` |
| `users_routes.router` | — | `routers/users.py` |
| `admin_routes.router` | — | `routers/admin.py` |
| `learning_path_routes.router` | `/api` | `routers/learning_path.py` |
| `tasks_routes.router` | — | `routers/tasks.py` |

#### Error Handlers

- `ValueError` → 400 with message
- Generic `Exception` → 500 with "Internal server error" + stack trace logged

---

### 4.2 Configuration (config.py)

**File:** `backend/app/config.py` (88 lines)

Uses `@lru_cache` singleton pattern via `get_settings()`. The `Settings` class reads from environment variables with defaults.

#### LLM Provider Config

| Variable | Default | Purpose |
|----------|---------|---------|
| `GEMINI_API_KEYS` | (from `GEMINI_API_KEY`) | Comma-separated list of Gemini keys |
| `GEMINI_API_KEY` | `""` | Fallback single key |
| `GEMINI_MODEL` | `"gemma-4-31b-it"` | Chat model |
| `GEMINI_VISION_MODEL` | `"gemma-4-31b-it"` | Vision model (for images) |
| `GEMINI_BASE_URL` | `"https://generativelanguage.googleapis.com/v1beta/openai"` | OpenAI-compatible endpoint |
| `OPENROUTER_API_KEYS` | (from `OPENROUTER_API_KEY`) | Comma-separated list |
| `OPENROUTER_API_KEY` | `""` | Fallback single key |
| `OPENROUTER_BASE_URL` | `"https://openrouter.ai/api/v1"` | OpenRouter endpoint |
| `EMBEDDING_MODEL` | `"nvidia/llama-nemotron-embed-vl-1b-v2:free"` | Embedding model |
| `LLM_MODEL` | `"gemini-3.6-flash"` | Legacy — overridden by GEMINI_MODEL |
| `TOPIC_EXTRACTION_MODEL` | `"google/gemma-4-26b-a4b-it:free"` | Model for syllabus→topics |
| `QUIZ_MODEL` | `"google/gemma-4-26b-a4b-it:free"` | Model for quiz generation |

#### RAG Config

| Variable | Default | Purpose |
|----------|---------|---------|
| `RAG_TOP_K` | `5` | Number of chunks to retrieve |
| `CHUNK_SIZE` | `512` | Token count per chunk |
| `CHUNK_OVERLAP_TOKENS` | `64` | Overlap between chunks |
| `IMAGE_MAX_BATCH_SIZE` | `5` | Images per embedding batch |
| `IMAGE_MAX_PER_PDF` | `50` | Max images extracted per PDF |
| `RRF_K` | `60` | RRF fusion constant |
| `HNSW_EF_SEARCH` | `40` | HNSW search breadth |
| `MAX_HISTORY_TURNS` | `8` | Recent conversation turns to include |
| `RAG_MIN_SIMILARITY` | `0.4` | Minimum cosine similarity threshold |
| `GATEKEEPER_ENABLED` | `false` | Enable/disable relevance filter |
| `BLOOM_VALIDATION_ENABLED` | `false` | Enable Bloom's validation |
| `QUERY_ENHANCER_ENABLED` | `true` | Enable multi-query expansion |
| `QUERY_ENHANCER_NUM_QUERIES` | `3` | Number of search queries to generate |
| `CURRICULUM_K` | `3` | Curriculum search top-K |
| `CURRICULUM_EF` | `40` | Curriculum HNSW ef |
| `CURRICULUM_THRESHOLD` | `0.6` | Curriculum match threshold |

#### JWT Config

| Variable | Default | Purpose |
|----------|---------|---------|
| `JWT_SECRET` | `""` | Signing key (⚠️ placeholder: `change_this_to_a_random_secret`) |
| `JWT_ALGORITHM` | `"HS256"` | Signing algorithm |
| `JWT_EXPIRE_MINUTES` | `1440` | Token expiry (24 hours) |

#### Knowledge Tracing Config

| Variable | Default | Purpose |
|----------|---------|---------|
| `DKT_ACTIVE` | `false` | Deep Knowledge Tracing toggle (dormant) |
| `MASTERY_THRESHOLD` | `0.7` | Mastery cutoff for recommendations |
| `BKT_LEARNING_RATE` | `0.15` | BKT learn rate |
| `BKT_P_INIT` | `0.15` | BKT initial mastery probability |
| `BKT_P_LEARN` | `0.15` | BKT transition probability |
| `BKT_P_GUESS` | `0.15` | BKT guess probability |
| `BKT_P_SLIP` | `0.10` | BKT slip probability |

#### SurrealDB Config

| Variable | Default | Purpose |
|----------|---------|---------|
| `SURREAL_URL` | `"ws://localhost:8000/rpc"` | WebSocket endpoint |
| `SURREAL_NS` | `"adaptive_learning"` | Namespace |
| `SURREAL_DB` | `"learning_platform"` | Database name |
| `SURREAL_USER` | `"root"` | Auth user |
| `SURREAL_PASS` | `"root"` | Auth password |

#### Multi-Key Parsing

`_parse_csv()` handles `GEMINI_API_KEYS` and `OPENROUTER_API_KEYS` — splits comma-separated strings into lists, falls back to single key if the multi-key env var is empty.

```python
@staticmethod
def _parse_csv(env_name: str, fallback: str) -> list[str]:
    val = os.getenv(env_name, "")
    if val:
        return [k.strip() for k in val.split(",") if k.strip()]
    if fallback:
        return [fallback]
    return []
```

#### Startup Warnings

The `__init__` method logs warnings if JWT_SECRET, OPENROUTER_API_KEY, or GEMINI_API_KEY are missing.

---

### 4.3 Database Layer (db.py)

**File:** `backend/app/db.py` (289 lines)

Manages a singleton `AsyncSurreal` connection with retry logic and schema initialization.

#### SurrealDBManager (singleton)

```python
class SurrealDBManager:
    _instance: Optional[AsyncSurreal] = None
    _lock = asyncio.Lock()
```

**`get_db()` (lines 20-45):**
1. Acquires `_lock`
2. Returns existing instance if available
3. Otherwise: tries up to 5 attempts with 2s delay
4. Each attempt calls `_connect_once()` with 30s timeout
5. Raises `ConnectionError` after all retries exhausted

**`_connect_once()` (lines 48-63):**
1. Creates `AsyncSurreal(url)`
2. Calls `instance.connect()`
3. Signs in with `SURREAL_USER` / `SURREAL_PASS`
4. Selects namespace and database via `instance.use(ns, db)`
5. Calls `_init_schema(instance)` — defines all tables, fields, indexes

**`health_check()` (lines 66-73):**
Runs `INFO FOR DB` query, returns boolean.

**`reset()` (lines 76-84):**
Closes and nullifies the singleton (for test cleanup).

#### Schema Initialization

**`_probe_dimension()` (lines 87-97):**
1. Calls `router.embed_text("probe")` with the configured embedding model
2. Validates dimension is an int between 64 and 8192
3. Returns dimension for HNSW index creation
4. This runs on **every startup** — dimension is dynamic based on model

**`_init_schema(db)` (lines 100-281):**
Executes a single large SurrealQL query defining all tables, fields, indexes, and a cascade-delete event. Key elements:

**Tables:**
- `text_chunk` — indexed document text chunks with HNSW vector index
- `image_chunk` — extracted diagram images with HNSW vector index
- `curriculum_chunk` — syllabus/curriculum content with HNSW vector index
- `course` — course metadata
- `course_topic` — structured topics with prerequisites, Bloom levels
- `document` — deduplication tracking via content hash
- `user` — auth users with bcrypt hashes
- `chat_message` — per-session conversation history
- `query_log` — analytics: every query asked
- `quiz` — saved quiz attempts
- `flashcard_set` — saved flashcard sets
- `knowledge_state` — per-student per-topic per-Bloom-level mastery
- `topic_prerequisite` — prerequisite DAG edges
- `question_log` — individual question correctness records

**Analyzers & Indexes:**
- `chunk_analyzer` — tokenizers `blank,punct` + filters `lowercase,snowball(english)`
- `text_search_idx` — BM25 fulltext index on `text_chunk.text`
- `text_embedding_idx` — HNSW cosine index on `text_chunk.embedding` with dynamic dimension
- `image_embedding_idx` — HNSW cosine on `image_chunk.embedding`
- `curriculum_embedding_idx` — HNSW cosine on `curriculum_chunk.embedding`
- Unique indexes on `user.email`, `user.user_id`, `course.course_code`, `document.(course_code, content_hash)`, `course_topic.(course_code, topic_name)`, `knowledge_state.(student_id, course_code, topic_id, bloom_level)`

**Cascade Delete Event:**
```sql
DEFINE EVENT IF NOT EXISTS course_cascade_delete ON TABLE course
WHEN $event = "DELETE" THEN {
    DELETE text_chunk WHERE course_code = $before.course_code;
    DELETE image_chunk WHERE course_code = $before.course_code;
    DELETE curriculum_chunk WHERE course_code = $before.course_code;
    DELETE course_topic WHERE course_code = $before.course_code;
    DELETE knowledge_state WHERE course_code = $before.course_code;
    DELETE question_log WHERE course_code = $before.course_code;
    DELETE topic_prerequisite WHERE course_code = $before.course_code;
};
```

**Error handling:** If schema init fails with "already exists" or "duplicate", it logs and continues. Other errors are raised.

---

### 4.4 Provider Router (provider_router.py)

**File:** `backend/app/provider_router.py` (468 lines)

The central LLM/embedding routing layer. Routes chat completions to Gemini and embeddings to OpenRouter, with multi-key rotation and automatic 429 handling.

#### KeyRing (lines 26-56)

Round-robin key pool with per-key cooldown on 429:

```python
class KeyRing:
    def __init__(self, keys: list[str]):
        self.keys = list(keys)
        self._index = 0
        self._cooldowns: dict[str, float] = {}    # key → cooldown end time
        self._backoffs: dict[str, float] = {}      # key → current backoff duration
```

- **`get_key()`**: Iterates through keys round-robin, skips cooldowned keys, returns the least-worst key if all are in cooldown
- **`report_429(key)`**: Puts key in cooldown, doubles backoff (10s → 20s → 40s → ... → 300s max)
- **`report_success(key)`**: Clears cooldown and backoff for the key

#### ProviderRouter (lines 59-468)

```python
class ProviderRouter:
    def __init__(self):
        # Gemini: chat completions
        self._gemini_keys = KeyRing(gemini_keys)
        self._gemini_base = settings.GEMINI_BASE_URL
        self._gemini_model = settings.GEMINI_MODEL
        self._gemini_vision_model = settings.GEMINI_VISION_MODEL

        # OpenRouter: embeddings
        self._or_keys = KeyRing(or_keys)
        self._or_base = settings.OPENROUTER_BASE_URL
        self._embedding_model = settings.EMBEDDING_MODEL

        self._client = httpx.AsyncClient(timeout=120, limits=...)
```

**`_resolve_chat_provider(model)` (lines 215-218):**
- If model contains `/` (e.g., `google/gemma-4-26b-it:free`), routes to OpenRouter
- Otherwise, routes to Gemini

**`chat()` (lines 220-250):**
1. Resolves provider based on model name
2. If images present, switches to vision model, builds multimodal content
3. POSTs to `/v1/chat/completions` via `_api_post`
4. Strips `<thought>...</thought>` tags from response
5. Returns content string

**`stream()` (lines 252-309):**
1. Same provider resolution as chat
2. POSTs with `stream: true`
3. Uses incremental UTF-8 decoder for SSE parsing
4. Yields `{"type": "thinking", "content": ...}` or `{"type": "content", "content": ...}`
5. Handles Google's `extra_content.google.thought` field

**`chat_with_schema()` (lines 311-355):**
1. Injects JSON schema into system message
2. Sets `response_format: {"type": "json_object"}`
3. Strips markdown fences from response
4. Returns parsed JSON dict

**`embed_text()`, `embed_text_batch()` (lines 359-379):**
Post to OpenRouter `/embeddings` endpoint.

**`embed_images()` (lines 381-430):**
1. Batches images (default batch size 5)
2. Builds multimodal inputs: `[{"type": "text"}, {"type": "image_url"}]`
3. Posts to OpenRouter embeddings
4. Tracks skipped/failed batches

**`_api_post()` (lines 100-146) — Core HTTP helper:**
1. Gets a key from KeyRing
2. POSTs with auth header
3. On 429: reports to KeyRing, retries up to 3 times
4. On 4xx: raises ValueError immediately
5. On timeout/5xx: retries with exponential backoff (2s, 4s)

**`health_check()` (lines 435-455):**
Tests Gemini model listing + OpenRouter model listing.

---

### 4.5 RAG Pipeline (rag.py)

**File:** `backend/app/rag.py` (382 lines)

Core document ingestion and retrieval pipeline.

#### RAGPipeline Class

**`ingest(course_code, document_title, text, topic, metadata)` (lines 28-85):**
1. Cleans text via `clean_text()`
2. Chunks via `chunk_text()` (512 tokens, 64 overlap)
3. Embeds all chunks in batch via `client.embed_text_batch()`
4. Extracts page numbers from `[Page N]` markers
5. Cleans markers from chunk text
6. Batch-inserts into `text_chunk` table
7. Returns `{chunks_ingested, course_code, document_title}`

**`ingest_images(course_code, document_title, image_items, topic, metadata)` (lines 87-141):**
1. Filters valid images (base64 > 100 chars)
2. Caps at `IMAGE_MAX_PER_PDF` (50)
3. Embeds via `client.embed_images()` with batch size limit
4. Inserts into `image_chunk` table

**`ingest_pdf(course_code, document_title, filepath, topic, metadata)` (lines 143-214):**
1. Calculates SHA-256 hash
2. Checks `document` table for duplicate hash → returns `already_ingested` if found
3. Extracts all pages via `extract_all_pages()` (text + images)
4. Tags text with `[Page N]` markers
5. Ingests text via `self.ingest()`
6. Ingests images via `self.ingest_images()`
7. Records ingestion in `document` table
8. Returns `{text_chunks, image_chunks, total_chunks, course_code, document_title}`

**`retrieve(query, course_code, top_k, topic, content_type)` (lines 216-298) — Hybrid Search:**

```
1. Embed query → query_embedding (via OpenRouter)
2. Vector search on text_chunk: HNSW <|k, ef|> + cosine similarity
3. Apply RAG_MIN_SIMILARITY (0.4) threshold
4. Convert similarity to distance: distance = 1.0 - similarity
5. Vector search on curriculum_chunk (if content_type is None)
6. Reciprocal Rank Fusion (RRF):
   score(doc) += 1 / (RRF_K + rank) for each result set
7. Sort by RRF score, take top_k
8. Return list of chunk dicts with chunk_id
```

RRF implementation:
```python
rrf_k = self.rrf_k  # default: 60
scores = {}
doc_map = {}
for rank, doc in enumerate(vector_hits):
    doc_id = str(doc["id"])
    doc_map[doc_id] = doc
    scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (rrf_k + rank + 1)
for rank, doc in enumerate(curr_hits):
    doc_id = str(doc["id"])
    if doc_id not in doc_map:
        doc_map[doc_id] = doc
    scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (rrf_k + rank + 1)
sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
text_results = [doc_map[doc_id] for doc_id in sorted_ids[:k]]
```

**`get_course_stats(course_code)` (lines 300-336):**
Returns total chunks, text/image breakdown, topics, documents, curriculum docs.

**`get_batch_stats(course_codes)` (lines 338-357):**
Batch version for course listing — single query per type with `IN` clause.

**`delete_course(course_code)` (lines 359-363):**
Deletes all text_chunk and image_chunk for the course.

**`list_courses()` (lines 369-382):**
Deduplicated list of all course_codes across text_chunk and image_chunk.

#### Utility: `calculate_file_hash()`

SHA-256 via 4KB blocks — used for document deduplication.

> **LaTeX TikZ — Hybrid Search / RRF Fusion:**
> ```latex
> \documentclass[tikz,border=10pt]{standalone}
> \usepackage{tikz}
> \usetikzlibrary{positioning,arrows.meta}
> \begin{document}
> \begin{tikzpicture}[
>   node distance=1.2cm and 2cm,
>   box/.style={rectangle, draw, rounded corners, minimum width=2.8cm, minimum height=0.9cm, align=center, font=\small\sffamily},
>   proc/.style={box, fill=blue!10},
>   data/.style={box, fill=green!10},
>   result/.style={box, fill=orange!10},
>   arrow/.style={-{Latex[length=2mm]}, thick}
> ]
> \node[font=\Large\bfseries\sffamily] at (0,6) {Hybrid Search --- BM25 + HNSW + RRF};
> \node[data] (query) at (0,4.5) {Student Query};
> \node[proc] (embed) at (-4,3) {Embed Query\\OpenRouter};
> \node[proc] (bm25) at (4,3) {BM25 Fulltext\\SurrealDB};
> \node[proc] (vtext) at (-6,1.5) {HNSW Search\\text\_chunk};
> \node[proc] (vcurr) at (-2,1.5) {HNSW Search\\curriculum\_chunk};
> \node[data] (vec) at (-4,0) {Vector results};
> \node[data] (bm) at (4,0) {BM25 results};
> \node[result] (rrf) at (0,-1.5) {RRF Fusion};
> \node[result] (final) at (0,-3.5) {Top-K Results};
> \draw[arrow] (query) -- (embed);
> \draw[arrow] (query) -- (bm25);
> \draw[arrow] (embed) -- (vtext);
> \draw[arrow] (embed) -- (vcurr);
> \draw[arrow] (vtext) -- (vec);
> \draw[arrow] (vcurr) -- (vec);
> \draw[arrow] (bm25) -- (bm);
> \draw[arrow] (vec) -- (rrf);
> \draw[arrow] (bm) -- (rrf);
> \draw[arrow] (rrf) -- (final);
> \node[font=\small\ttfamily, fill=gray!5, rounded corners] at (5,-1.5) {RRF = $\sum 1/(60+rank)$};
> \end{tikzpicture}
> \end{document}
> ```

---

### 4.6 Query Engine (query_engine.py)

**File:** `backend/app/query_engine.py` (430 lines)

Builds prompts, orchestrates retrieval + LLM calls, enforces citations.

#### Prompt Builders

**`build_tutor_system_prompt(course_name, course_code, language, mastery, bloom_level)` (lines 58-102):**

**`build_context_window(chunks, history, max_turns)` (lines 105-157):**
1. **Empty-chunks guard (line 110-111):** If no chunks retrieved, returns `"NOTE: No relevant course materials were found for this question. Answer using general knowledge — no citations required."`
2. Separates text and image chunks
2. Formats text chunks as `<Text N: Title, Slide N>` blocks
3. Formats image chunks as `<Image N: Title, Slide N>` blocks
4. Builds "VALID CITATIONS LIST" from all chunks
5. Appends conversation history (last 8 turns)
6. Truncates older history with note

**`build_tutor_prompt(query, course_code, course_name, chunks, history, language, mastery, bloom_level)` (lines 157-174):**
Combines system prompt + context window + sanitized student query into messages array.

#### QueryEngine Class

**`query_stream()` (lines 235-344) — SSE streaming endpoint:**

Full pipeline:
```
1. Get course context (name, docs, curriculum)
2. Gatekeeper: check relevance (LLM call #1)
3. Query Enhancer: generate 3 search queries (LLM call #2)
4. For each search query: retrieve chunks via hybrid search
5. Deduplicate chunks by ID, cap at top_k * 2
6. Build tutor prompt with chunks + history
7. Strategy generation (LLM call #3): 2-3 sentence outline → yield as "thinking" event
8. Stream response (LLM call #4): async SSE chunks → yield as "content" events
9. Verifier: check grounding (LLM call #5)
10. Extract cited sources from response text
11. Yield "metadata" event with verification + citations
```

Strategy step (lines 301-309):
```python
strategy_prompt = messages + [
    {"role": "user", "content": "Briefly outline your strategy for answering this student's question..."}
]
strategy_text = await client.chat(strategy_prompt, temperature=0.2, max_tokens=150)
```

**`query()` (lines 346-427) — Non-streaming variant:**

Same pipeline without SSE streaming. Returns dict with `response`, `cited_sources`, `chunks_retrieved`.

Additional post-processing in non-streaming mode:
1. Verification: if invalid, appends `[Verification Note: ...]`
2. Citation validation: if invalid, calls `remove_uncited_claims()`

#### Auxiliary Functions

**`extract_cited_sources(response_text, chunks)` (lines 33-56):**
Matches `[Source: title, Slide/Page N]` citations in response back to retrieved chunks using `extract_all_citations()` + `parse_citation()`.

**`_normalize_cited_sources(sources)` (lines 21-30):**
Standardizes citation dict format.

> **LaTeX TikZ — RAG Pipeline Flow:**
> ```latex
> \documentclass[tikz,border=10pt]{standalone}
> \usepackage{tikz}
> \usetikzlibrary{positioning,arrows.meta}
> \begin{document}
> \begin{tikzpicture}[
>   node distance=1.2cm and 2cm,
>   step/.style={rectangle, draw, rounded corners, minimum width=3cm, minimum height=0.9cm, align=center, font=\small\sffamily},
>   llm/.style={step, fill=orange!15},
>   rag/.style={step, fill=blue!10},
>   arrow/.style={-{Latex[length=2mm]}, thick}
> ]
> \node[font=\Large\bfseries\sffamily] at (0,8.5) {RAG Pipeline --- Full Query Flow};
> \node[step] (s1) at (0,7) {1. Gatekeeper\\Relevance Check};
> \node[step] (s2) at (0,5.5) {2. Query Enhancer\\3 search queries};
> \node[rag] (s3) at (0,4) {3. Hybrid Retrieval\\BM25 + HNSW + RRF};
> \node[step] (s4) at (0,2.5) {4. Build Context Window\\Chunks + History};
> \node[llm] (s5) at (0,1) {5. Strategy Generation\\LLM call};
> \node[llm] (s6) at (0,-0.5) {6. Streaming Answer\\LLM call};
> \node[step] (s7) at (0,-2) {7. Verifier\\Grounding check};
> \node[step] (s8) at (0,-3.5) {8. Citation Extraction\\Regex match};
> \node[step] (s9) at (0,-5) {9. Persist Results\\query\_log + chat\_history};
> \draw[arrow] (s1) -- (s2);
> \draw[arrow] (s2) -- (s3);
> \draw[arrow] (s3) -- (s4);
> \draw[arrow] (s4) -- (s5);
> \draw[arrow] (s5) -- (s6);
> \draw[arrow] (s6) -- (s7);
> \draw[arrow] (s7) -- (s8);
> \draw[arrow] (s8) -- (s9);
> \end{tikzpicture}
> \end{document}
> ```

---

### 4.7 Authentication (auth.py)

**File:** `backend/app/auth.py` (144 lines)

Self-hosted JWT authentication with bcrypt password hashing.

#### Password Hashing (lines 32-40)

```python
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        return False
```

#### JWT Operations (lines 43-63)

**`create_access_token(data, expires_minutes)` (lines 43-49):**
1. Copies data dict
2. Adds `exp` = UTC now + `JWT_EXPIRE_MINUTES` (default 1440 = 24h)
3. Encodes with `jose.jwt.encode()` using `JWT_SECRET` and `JWT_ALGORITHM`

**`decode_token(token)` (lines 52-63):**
1. Decodes with `jose.jwt.decode()`
2. On `JWTError`: raises `HTTPException(401, "Invalid or expired token")`

#### User Management (lines 66-93)

**`get_user_by_email(email)` (lines 66-82):**
Queries SurrealDB `user` table, returns dict with `id`, `email`, `hashed_password`, `role`, `created_at`.

**`_create_user(email, hashed_password, role)` (lines 85-93):**
Creates user with UUID, lowercased email, default name from email prefix.

#### FastAPI Dependencies (lines 96-144)

**`get_current_user(token)` (lines 96-121):**
Standard `Depends()`-compatible: decodes Bearer token, looks up user by email, returns user dict or 401.

**`get_current_user_from_request(request)` (lines 124-132):**
Reads `request.state.user` set by auth middleware. Returns 401 if missing.

**`require_role(*allowed_roles)` (lines 135-143):**
Returns a dependency checker that validates `request.state.user.role` is in allowed set. Returns 403 on role mismatch.

> **LaTeX TikZ — Authentication & Authorization Flow:**
> ```latex
> \documentclass[tikz,border=10pt]{standalone}
> \usepackage{tikz}
> \usetikzlibrary{positioning,arrows.meta,shapes.geometric}
> \begin{document}
> \begin{tikzpicture}[
>   node distance=1.2cm and 2.5cm,
>   box/.style={rectangle, draw, rounded corners, minimum width=2.5cm, minimum height=0.9cm, align=center, font=\small\sffamily},
>   actor/.style={box, fill=green!10},
>   server/.style={box, fill=blue!10},
>   middleware/.style={box, fill=yellow!10},
>   decision/.style={diamond, draw, aspect=1.5, align=center, font=\small\sffamily, inner sep=3pt},
>   arrow/.style={-{Latex[length=2mm]}, thick}
> ]
> \node[font=\Large\bfseries\sffamily] at (1,5) {Authentication \& Authorization Flow};
> \node[actor] (login) at (-4,3.5) {Login Form};
> \node[server] (auth) at (-4,1.5) {POST /auth/login};
> \node[server] (jwt) at (-4,-0.5) {JWT Creation};
> \node[actor] (store) at (-4,-2.5) {Zustand Store};
> \draw[arrow] (login) -- node[right,font=\small\sffamily] {form-encoded} (auth);
> \draw[arrow] (auth) -- node[right,font=\small\sffamily] {bcrypt} (jwt);
> \draw[arrow] (jwt) -- node[right,font=\small\sffamily] {token+role} (store);
> \node[box] (req) at (2.5,3.5) {Any Request};
> \node[middleware] (mw) at (2.5,2) {auth\_middleware};
> \node[decision] (valid) at (2.5,0) {JWT valid?};
> \node[box] (pub) at (-1,0) {Public?};
> \node[box] (route) at (2.5,-2) {Route handler};
> \draw[arrow] (req) -- (mw);
> \draw[arrow] (mw) -- (valid);
> \draw[arrow] (valid) -- node[right,font=\small\sffamily] {Yes} (route);
> \draw[arrow] (valid) -- node[above,font=\small\sffamily] {No} (pub);
> \draw[arrow] (pub) -- node[above,font=\small\sffamily] {No} (-1,-0.5);
> \node at (-1,-0.8) [font=\small\sffamily] {401};
> \node[decision] (role) at (6,2) {Role?};
> \node[box] (rroute) at (6,-0.5) {Handler};
> \node[box] (redir) at (9,2) {Redirect};
> \draw[arrow] (route) -- (role);
> \draw[arrow] (role) -- node[right,font=\small\sffamily] {OK} (rroute);
> \draw[arrow] (role) -- node[above,font=\small\sffamily] {Wrong} (redir);
> \end{tikzpicture}
> \end{document}
> ```

---

### 4.8 Validation (validation.py)

**File:** `backend/app/validation.py` (103 lines)

Input sanitization, injection detection, and constraint constants.

#### Constants

```python
MAX_COURSE_CODE_LENGTH = 20
MAX_SESSION_ID_LENGTH = 50
MAX_TOPIC_LENGTH = 100
MAX_QUESTION_LENGTH = 1000
MAX_COURSE_NAME_LENGTH = 100
MAX_DESCRIPTION_LENGTH = 500
MAX_LANGUAGE_LENGTH = 20
MAX_FILE_SIZE = 15 * 1024 * 1024   # 15MB
MAX_IMAGE_SIZE = 5 * 1024 * 1024    # 5MB per image
MAX_IMAGES_PER_MESSAGE = 5
ALLOWED_IMAGE_MIMES = {"image/jpeg", "image/png"}
```

#### Sanitization Functions

**`sanitize_id(id_str)` (lines 22-40):**
Replaces non-alphanumeric chars with `_`, prepends `id_` if starts with `.` or `_`, truncates to 50 chars.

**`validate_id(id_str)` (lines 42-49):**
Raises ValueError on empty, too long, or invalid characters.

**`validate_course_code(course_code)` (lines 51-57):**
Trims, truncates, sanitizes. Never raises — auto-fixes.

**`sanitize_text(text, max_length)` (lines 59-63):**
Trims and truncates.

#### Injection Detection (lines 65-96)

Regex patterns for prompt injection attempts:
```python
INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules)", re.I),
    re.compile(r"disregard\s+(the\s+)?(previous|prior|above|system)", re.I),
    re.compile(r"forget\s+(everything|all|your\s+instructions)", re.I),
    re.compile(r"you\s+are\s+now\s+", re.I),
    re.compile(r"new\s+(instructions|rules|system\s+prompt)", re.I),
    re.compile(r"act\s+as\s+(if|a|an)\s+", re.I),
    re.compile(r"</?(system|assistant|user)>", re.I),
    re.compile(r"\[/?(INST|SYS)\]", re.I),
    re.compile(r"reveal\s+(your\s+)?(system\s+prompt|instructions)", re.I),
]
```

**`sanitize_student_query(text)` (lines 78-96):**
1. Strips chat role markers (`<system>`, `[INST]`, etc.)
2. Replaces injection phrases with `[filtered]`
3. Truncates to `MAX_QUESTION_LENGTH`

---

### 4.9 Gatekeeper (gatekeeper.py)

**File:** `backend/app/gatekeeper.py` (82 lines)

LLM-as-a-judge relevance filter. Determines if a student's query is relevant to the course materials.

```python
class Gatekeeper:
    async def check_and_enrich(query, course_code, context) -> (bool, str, str|None):
        # Returns: (is_relevant, enriched_query, refusal_message)
```

**Prompt:**
- System message includes course description, available documents with previews, curriculum topics
- Instructs LLM to rewrite query for better vector search if relevant
- Output format is JSON with `relevant`, `enriched_query`, `refusal_message`

**Behavior:**
- On success: returns parsed JSON from `chat_with_schema`
- On error: defaults to `(True, query, None)` — allows the query through

**Controlled by:** `settings.GATEKEEPER_ENABLED` (default: `false`)

---

### 4.10 Verifier (verifier.py)

**File:** `backend/app/verifier.py` (66 lines)

LLM-as-a-judge grounding verifier. Checks if the generated answer is factually supported by retrieved chunks.

```python
class Verifier:
    async def verify_answer(query, answer, chunks, course_code) -> (bool, str):
```

**Prompt:**
- System: "Check if the generated answer is accurately grounded in the provided course materials"
- Rules: mark invalid if info not in materials, or if citations are missing
- Output format: `{"valid": bool, "reason": str | null}`

**Behavior:**
- Passes chunk texts (first 4000 chars) as context
- On error: defaults to `(True, None)` — assumes valid

---

### 4.11 Chunker (chunker.py)

**File:** `backend/app/chunker.py` (108 lines)

Sentence-aware text chunking using tiktoken (cl100k_base).

#### `token_count(text)` (lines 17-18)
Uses tiktoken `cl100k_base` encoding.

#### `chunk_text(text, chunk_size, overlap_tokens)` (lines 20-65)

Algorithm:
1. Split text on sentence boundaries (`[.!?]\s+`)
2. Accumulate sentences until token count exceeds `chunk_size` (default 512)
3. Create chunk from accumulated sentences
4. Overlap: keep last 3 sentences (max), find their char position
5. Continue from overlap

Returns: `list[(chunk_text, start_char, end_char)]`

#### `clean_text(text)` (lines 68-79)
- Preserves `[Page N]` markers via temporary replacement (`__PAGE_N__`)
- Collapses whitespace
- Removes control characters
- Removes bare `Page N` text (without brackets)
- Removes hyphenated line breaks (`-\n`)

#### `extract_page_for_chunk(chunk_text, full_text, start_index)` (lines 82-108)
Finds the last `[Page N]` marker before or within the chunk's start position. Returns page number (default 1).

---

### 4.12 Citation Enforcement (citation.py)

**File:** `backend/app/citation.py` (108 lines)

Regex-based citation extraction and validation.

#### Patterns

```python
CITATION_RE = re.compile(r"\[Source:\s*[^\]]+\]", re.IGNORECASE)
```

#### Functions

**`parse_citation(citation_text)` (lines 19-31):**
Extracts `(title, page)` tuple from `[Source: Title, Slide 5]` or `[Source: Title, Page 5]` or `[Source: Title, 5]`.

**`has_citation(text)` (lines 34-35):**
Checks if any citation pattern exists.

**`extract_all_citations(text)` (lines 38-41):**
Returns all `[Source: ...]` matches.

**`remove_uncited_claims(text)` (lines 44-61):**
1. Sentence-tokenizes with NLTK
2. Keeps sentences with citations, questions, short sentences, or question-like starts
3. Appends `[Note: N claim(s) could not be verified...]`

**`validate_citations(response, chunks)` (lines 68-108):**
1. Extracts all citations from response
2. Builds lookup set from chunks: `{(title.lower(), page)}`
3. Matches each citation (exact then loose)
4. Returns `{valid (≥80%), total_citations, valid_citations, coverage, citations, details}`

---

### 4.13 Knowledge State (knowledge_state.py)

**File:** `backend/app/knowledge_state.py` (126 lines)

Per-student per-topic per-Bloom-level mastery tracking using a simplified BKT model.

#### Constants

```python
LEARNING_RATE = 0.15

BLOOM_PROMPTS = {
    1: "Ask recall questions...",
    2: "Ask for explanations...",
    3: "Ask the student to apply...",
    4: "Ask the student to break down relationships...",
    5: "Ask the student to justify or critique...",
    6: "Ask the student to design or generate...",
}
BLOOM_LABELS = {1: "Remember", 2: "Understand", 3: "Apply", 4: "Analyze", 5: "Evaluate", 6: "Create"}
```

#### KnowledgeStateManager

**`get_state(student_id, course_code, topic_id, bloom_level)` (lines 19-27):**
Queries `knowledge_state` table, returns record or default state.

**`update_state(student_id, course_code, topic_id, bloom_level, is_correct)` (lines 51-101):**

Mastery update formula:
```python
if is_correct:
    mastery += LEARNING_RATE * (1 - mastery)   # asymptotic approach to 1.0
    streak += 1
else:
    mastery -= LEARNING_RATE * mastery          # decay toward 0.0
    streak = 0

mastery = max(0.0, min(1.0, mastery))

# Confidence: weighted by attempts
correct_rate = correct / total
confidence = 1.0 - ((1.0 - correct_rate) / (1.0 + total * 0.1))
```

Creates or updates the `knowledge_state` record. Also logs to `question_log`.

**`get_topic_summary(student_id, course_code, topic_id)` (lines 37-49):**
Averages mastery and confidence across all Bloom levels for a topic.

**`_log_question()` (lines 103-108):**
Logs to `question_log` table for gap detection analytics.

**`_default_state()` (lines 110-126):**
Returns zeroed-out state with current timestamp.

---

### 4.14 Curriculum Manager (curriculum.py)

**File:** `backend/app/curriculum.py` (150 lines)

Handles curriculum PDF ingestion, listing, and topic relevance checking.

#### CurriculumManager

**`ingest_curriculum(course_code, document_title, filepath, topic)` (lines 12-93):**
1. Validates course code
2. Calculates SHA-256, checks `document` table for duplicates
3. Extracts pages via `extract_all_pages()`
4. Embeds each page via `client.embed_text_batch()`
5. Inserts into `curriculum_chunk` table
6. Auto-heals missing SurrealDB fields (catches `InternalError`, extracts field name, runs `DEFINE FIELD`)
7. Records in `document` table
8. Calls `extract_topics_from_syllabus()` + `store_course_topics()` via LLM

**`list_curriculum(course_code)` (lines 95-101):**
Returns sorted list of source titles from `curriculum_chunk`.

**`check_topic_in_curriculum(course_code, query)` (lines 117-150):**
1. Embeds query
2. HNSW vector search on `curriculum_chunk`
3. If max similarity > `CURRICULUM_THRESHOLD` (0.6): topic is covered
4. Falls back to searching `text_chunk`

---

### 4.15 Topic Extraction (topics.py)

**File:** `backend/app/topics.py` (159 lines)

LLM-powered extraction of structured topics from syllabus text.

**`extract_topics_from_syllabus(syllabus_text)` (lines 50-71):**
1. Calls `client.chat_with_schema()` with `TOPIC_EXTRACTION_PROMPT`
2. Schema: `{topics: [{topic_name, subtopics, prerequisites, bloom_level, learning_objectives}]}`
3. Uses `settings.TOPIC_EXTRACTION_MODEL` (default: `google/gemma-4-26b-a4b-it:free`)
4. Returns empty list on any error

**`store_course_topics(course_code, topics)` (lines 74-106):**
1. Deletes existing `course_topic` and `topic_prerequisite` for course
2. Inserts each topic with `order_index`
3. Creates prerequisite edges in `topic_prerequisite` table

**`get_course_topics(course_code)` (lines 109-128):**
Returns ordered list of topics with subtopics, prerequisites, Bloom levels.

**`get_topic_coverage(course_code)` (lines 131-159):**
For each topic, checks if any `text_chunk` has a matching topic tag. Returns `covered`/`missing` status per topic.

---

### 4.16 Learning Path (learning_path.py)

**File:** `backend/app/learning_path.py` (69 lines)

Prerequisite DAG traversal for Zone of Proximal Development recommendations.

#### TopicPrerequisiteGraph

**`get_graph(course_code)` (lines 7-19):**
Queries `topic_prerequisite` for `hard` type edges. Builds adjacency dict `{topic → set(prerequisites)}`.

**`get_zpd_candidates(student_id, course_code, mastery_threshold)` (lines 21-54):**

Algorithm:
1. Get all knowledge states for the student
2. Build per-topic max mastery map
3. Build prerequisite graph
4. For each topic:
   - If no prerequisites: candidate if mastery < threshold
   - If has prerequisites: candidate if ALL prereqs mastered AND topic not mastered
   - Priority = `(threshold - mastery) * (in-degree + out-degree)` — topics with more connections get higher priority
5. Return top 5 candidates sorted by priority

**`add_prerequisite(course_code, topic_from, topic_to, prereq_type)` (lines 56-61):**
Creates a prerequisite edge in `topic_prerequisite`.

**`get_prerequisites(course_code, topic_id)` (lines 63-69):**
Returns list of prerequisite topic names.

---

### 4.17 Analytics (analytics.py)

**File:** `backend/app/analytics.py` (236 bytes — 236 lines)

Analytics queries: query logging, unanswered questions, coverage, topic insights.

#### Functions

**`log_query(question, course_code, response, cited_sources, user_id)` (lines 13-37):**
Creates a `query_log` record with sanitized question, response preview (200 chars), out-of-scope flag.

**`get_unanswered_questions(course_code)` (lines 40-57):**
Returns query_log entries where `out_of_scope = true`.

**`get_coverage(course_code)` (lines 60-75):**
Aggregates `cited_sources` across all query_log entries — counts how many times each source was cited.

**`get_analytics(course_code)` (lines 116-159):**
Returns:
- Top 10 most asked questions with counts
- Questions per day (date histogram)
- Weak topics (few hits, no chunks)
- Suggested revision topics (no hits, no chunks)
- Topic coverage from curriculum
- Recent 10 questions

**`get_my_analytics(user_email, course_code)` (lines 171-216):**
Same as `get_analytics` but filtered by `user_id`. Adds Bloom's mastery per level.

**`get_student_bloom_mastery(student_id, course_code)` (lines 162-168):**
Returns dict: `{bloom_level: mastery_score}` from `knowledge_state`.

---

### 4.18 PDF Extractor (pdf_extractor.py)

**File:** `backend/app/pdf_extractor.py` (113 lines)

Extracts text AND images from PDFs for multimodal RAG.

#### Data Classes

```python
@dataclass
class ImageContent:
    b64_str: str          # base64-encoded image data
    mime_type: str        # image/jpeg, image/png, etc.
    valid: bool
    bytes_size: int

@dataclass
class PageContent:
    page_num: int
    text: str
    images: list[ImageContent]
```

#### Image Detection

Magic byte detection for supported formats:
```python
JPEG_MAGIC = b"\xFF\xD8\xFF"
PNG_MAGIC = b"\x89\x50\x4E\x47"
WEBP_MAGIC = b"\x57\x45\x42\x50"  # via RIFF container
```

**`_extract_page_images(page)` (lines 70-97):**
1. Gets `/Resources/XObject` dict from PDF page
2. For each `xobj` with `/Subtype == /Image`:
   - Gets raw bytes via `xobj.get_data()`
   - Validates via magic bytes
   - Skips images < 1000 bytes (likely garbage)
   - Returns `ImageContent` with base64

**`_sync_extract_all_pages(source)` (lines 100-109):**
Runs PyPDF synchronous extraction in thread.

**`extract_all_pages(source)` (lines 112-113):**
Wraps sync extraction in `asyncio.to_thread()`.

---

### 4.19 Query Enhancer (query_enhancer.py)

**File:** `backend/app/query_enhancer.py` (76 lines)

Generates multiple diverse search queries from a single student question.

**`generate_search_queries(query, course_context, num_queries)` (lines 22-76):**
1. Builds system prompt with course context (documents, curriculum)
2. Instructs LLM to generate N queries targeting different aspects
3. Uses `chat_with_schema` with `{queries: [string]}` schema
4. Returns generated queries, falls back to `[query]` on error

Controlled by `settings.QUERY_ENHANCER_ENABLED` and `settings.QUERY_ENHANCER_NUM_QUERIES` (default 3).

---

### 4.20 Paper Generator (paper_generator.py)

**File:** `backend/app/paper_generator.py` (109 lines)

Generates exam papers with Bloom's taxonomy-aligned questions.

**`generate_paper(course_code, total_marks, difficulty, topics, chunks, bloom_levels)` (async):**

1. Builds expert examiner system prompt
2. Defines JSON schema for paper structure (sections × questions × MCQ/short_answer/long_answer)
3. Uses `client.chat_with_schema()` to generate structured output
4. Returns parsed paper JSON

---

### 4.21 Bloom Classifier (bloom_classifier.py)

**File:** `backend/app/bloom_classifier.py` (81 lines)

Classifies student questions into Bloom's Taxonomy levels via LLM.

**`classify_bloom_level(question)` (lines 37-54):**
- Simple LLM call: prompts model to return integer 1-6
- Caches results in `_bloom_cache` dict (in-memory, no eviction)

**`classify_bloom_levels(questions)` (lines 57-81):**
- Batched version: sends all questions in one LLM call
- Returns array of `int | None` — `None` for classification failures

---

### 4.22 Gap Detection (gap_detection.py)

**File:** `backend/app/gap_detection.py` (73 lines)

Detects when quiz accuracy drops significantly across Bloom levels.

**`detect_gaps(student_id, course_code, topic_id)` (lines 16-60):**
1. Queries `question_log` for quiz source, groups by bloom_level
2. Requires ≥3 attempts per level (`MIN_ATTEMPTS_PER_LEVEL`)
3. Compares adjacent levels: if accuracy drops > 25% and below mastery threshold → gap
4. Returns sorted list of gaps: `{bloom_level, accuracy, lower_level_accuracy, gap, attempts}`

**`should_trigger_diagnostic(student_id, course_code)` (lines 63-65):**
Returns true if ≥2 gaps detected.

---

### 4.23 Evaluator (evaluator.py)

**File:** `backend/app/evaluator.py` (264 lines)

RAGAS-style evaluation metrics using LLM-as-a-judge.

#### RG Class (RAGAS-style metrics)

**`faithfulness(response, contexts)` (lines 12-63):**
Counts supported vs unsupported claims via LLM. Returns 0.0-1.0.

**`answer_relevancy(query, response)` (lines 65-93):**
Rates how well the response addresses the query. Returns 0.0-1.0.

**`context_precision(query, retrieved_chunks)` (lines 95-132):**
Finds fraction of retrieved chunks relevant to the query. Returns 0.0-1.0.

**`context_recall(query, response, retrieved_chunks)` (lines 134-172):**
Estimates what fraction of required information was retrieved. Returns 0.0-1.0.

**`run_full_eval(query, response, retrieved_chunks)` (lines 174-194):**
Runs all 4 metrics, computes overall average.

#### RAGASEvaluator Class (lines 197-264)

Provides `evaluate()` and `evaluate_batch()` interfaces, plus `print_report()` for formatted output.

---

### 4.24 Scheduler (scheduler.py)

**File:** `backend/app/scheduler.py` (85 lines)

Spaced repetition scheduler using SM-2-like algorithm.

**`_mastery_to_rating(mastery)` (lines 47-51):**
- ≥0.9 → 5, ≥0.7 → 4, ≥0.5 → 3, ≥0.3 → 2, else 1

**`_schedule_simple(rating, streak)` (lines 53-63):**
- Rating < 3 → 1 day
- Rating 3, streak 0 → 1; streak ≥ 1 → 6^(streak-1) days
- Rating 4, streak 0 → 1; streak ≥ 1 → 6*(3)^(streak-1) days
- Rating 5, streak 0 → 1; streak ≥ 1 → 6*(4)^(streak-1) days

**`run_nightly_scheduler()` (lines 65-76):**
Queries all `knowledge_state` records, maps mastery to rating, updates `next_review_at`.

**`schedule_on_quiz(student_id, course_code, topic_id, bloom_level, mastery, streak)` (lines 78-84):**
Single record update after quiz.

---

### 4.25 Knowledge Tracing (knowledge_tracing.py)

**File:** `backend/app/knowledge_tracing.py` (60 lines)

Bayesian Knowledge Tracing implementation.

#### BKTModel

Parameters: `p_init` (initial mastery), `p_learn` (transition probability), `p_guess` (guess probability), `p_slip` (slip probability).

**`predict(prior, is_correct)` (lines 25-34):**

```
p_correct = prior * (1 - p_slip) + (1 - prior) * p_guess
if is_correct:
    posterior = prior * (1 - p_slip) / p_correct
else:
    posterior = prior * p_slip / (1 - p_correct)
result = posterior + (1 - posterior) * p_learn
```

**`mastery_from_sequence(observations, initial)` (lines 35-39):**
Sequentially applies `predict()` over a list of boolean observations.

---

### 4.26 Deep KT (deep_kt.py)

**File:** `backend/app/deep_kt.py` (21 lines)

Deep Knowledge Tracing LSTM skeleton. **Dormant** — requires `DKT_ACTIVE=True` and `torch`.

```python
class DKTModel:
    def __init__(self, n_skills, hidden_size=128):
        self._model = None  # not implemented

    def predict(self, student_id) -> dict:
        if not settings.DKT_ACTIVE:
            return {}
        return {}  # stub
```

---

### 4.27 Chat History (chat_history.py)

**File:** `backend/app/chat_history.py` (42 lines)

Simple CRUD for per-session chat messages.

**`get_course_history(course_code, session_id, user_id)` (lines 10-19):**
Queries `chat_message` ordered by timestamp, optionally filtered by user.

**`add_message(course_code, session_id, role, content, user_id)` (lines 21-26):**
Creates `chat_message` record with role (`user`/`assistant`), content, and optional user_id.

**`clear_course_history(course_code, session_id, user_id)` (lines 28-36):**
Deletes all messages matching course + session (optionally user).

---

### 4.28 Courses (courses.py)

**File:** `backend/app/courses.py` (73 lines)

Course CRUD operations.

**`get_all_courses_data()` — `SELECT * FROM course ORDER BY created_at DESC`**

**`create_course(course_code, course_name, description, icon)` — Validates, checks duplicate, creates.**

**`update_course(course_code, course_name, description, icon)` — Partial update via `MERGE`.**

**`delete_course(course_code)` — Deletes course + related chunks via SurrealDB cascade event.**

---

### 4.29 Celery Tasks (tasks.py)

**File:** `backend/app/tasks.py` (152 lines)

Celery worker configuration and background tasks. 3 task types.

#### Celery App

```python
celery_app = Celery("adaptive_learner")
_worker_loop = asyncio.new_event_loop()  # shared event loop for all async tasks
```

Config:
- Broker/backend: Redis (default `redis://redis:6379/0`)
- Serialization: JSON
- Task tracking: enabled
- Acks late: true (redeliver if worker crashes)
- Prefetch: 1 (fair scheduling)

#### Tasks

**`ingest_pdf_task(course_code, document_title, filepath, topic, metadata)` (lines 43-57):**
1. Creates `RAGPipeline()` instance
2. Runs `rag.ingest_pdf()` in the shared event loop
3. Cleans up temp file in `finally`
- `max_retries=3, autoretry_for=(ValueError,)`

**`ingest_curriculum_task(course_code, document_title, filepath, topic)` (lines 60-73):**
Same pattern for curriculum ingestion.
- `max_retries=3, autoretry_for=(ValueError,)`

**`process_query_task(course_code, session_id, question, user_email, language, mastery, bloom_level, top_k, image_ids, history)` (lines 76-152):**

This is the **async query workhorse** — decouples LLM calls from the HTTP lifecycle.

1. Gets Redis client via `get_redis()` module-level singleton
2. Defines an inner `async _run()` coroutine that:
   a. Creates `QueryEngine()` instance
   b. If `image_ids` provided: loads images from `uploads/chat/` dir, base64-encodes, maps MIME types
   c. Calls `engine.query_stream()` — runs the full RAG pipeline
   d. For each SSE chunk (`thinking`/`content`/`metadata`): RPUSHes JSON to `query_progress:{task_id}`
   e. On completion: creates `query_log` record + persists both user and assistant messages via `add_message()` / `chat_history.py`
   f. RPUSHes `{"type": "done"}`
3. On exception: RPUSHes `{"type": "error", "content": str(e)}`
4. `finally`: sets TTL 600s on the Redis key (auto-cleanup)
5. Returns `{"status": "done"}` — Celery result (not used by frontend)

Key design decisions:
- `max_retries=1` — no retry on failure, error is streamed to frontend
- Request ID propagation via Celery signals (same as other tasks)
- Frontend recovers in-flight tasks from `sessionStorage` on page refresh

#### Request ID Propagation

```python
@signals.before_task_publish.connect
def propagate_request_id(headers, **kwargs):
    rid = request_id_var.get()
    if rid:
        headers["request_id"] = rid

@signals.task_prerun.connect
def restore_request_id(task, **kwargs):
    headers = getattr(task.request, "headers", {}) or {}
    rid = headers.get("request_id", "")
    if rid:
        request_id_var.set(rid)
```

> **LaTeX TikZ — Celery Task Architecture:**
> ```latex
> \documentclass[tikz,border=10pt]{standalone}
> \usepackage{tikz}
> \usetikzlibrary{positioning,arrows.meta}
> \begin{document}
> \begin{tikzpicture}[
>   node distance=1.2cm and 2.5cm,
>   task/.style={rectangle, draw, rounded corners, minimum width=3cm, minimum height=1cm, align=center, font=\small\sffamily},
>   infra/.style={rectangle, draw, rounded corners, minimum width=2.5cm, minimum height=0.8cm, align=center, font=\small\sffamily, fill=gray!10},
>   arrow/.style={-{Latex[length=2mm]}, thick}
> ]
> \node[font=\Large\bfseries\sffamily] at (0,5) {Celery Task Architecture --- 3 Types};
> \node[infra] (redis) at (0,3) {Redis broker + backend};
> \node[task] (ingest) at (-4,0.5) {ingest\_pdf\_task};
> \node[task] (curr) at (0,0.5) {ingest\_curriculum\_task};
> \node[task] (query) at (4,0.5) {process\_query\_task};
> \node[below=of ingest, font=\footnotesize\sffamily, text width=3cm, align=center] {RAGPipeline\\max\_retries=3\\rm temp file};
> \node[below=of curr, font=\footnotesize\sffamily, text width=3cm, align=center] {CurriculumManager\\max\_retries=3\\topic extraction};
> \node[below=of query, font=\footnotesize\sffamily, text width=3cm, align=center] {QueryEngine\\max\_retries=1\\RPUSH SSE chunks\\TTL 600s};
> \draw[arrow] (redis) -- (ingest);
> \draw[arrow] (redis) -- (curr);
> \draw[arrow] (redis) -- (query);
> \end{tikzpicture}
> \end{document}
> ```

---

### 4.30 Redis Client (redis_client.py)

**File:** `backend/app/redis_client.py` (15 lines)

Minimal Redis singleton for Celery task streaming, used by `process_query_task` and `query_stream/{task_id}` endpoint.

```python
import os
import redis as _redis

_client = None

def get_redis():
    global _client
    if _client is None:
        _client = _redis.from_url(
            os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0"),
            decode_responses=True,
        )
    return _client
```

Key points:
- Module-level singleton: `_client = None`, initialized on first call
- Reads `CELERY_BROKER_URL` env var (same as Celery config) — defaults to `redis://redis:6379/0`
- `decode_responses=True` — returns strings, not bytes
- Used in `routers/query.py` (`/query-stream/{task_id}` LRANGE polling) and `tasks.py` (`process_query_task` RPUSH)

---

### 4.31 Dependencies (deps.py)

**File:** `backend/app/deps.py` (21 lines)

FastAPI dependency injection — pulls services from `app.state`.

```python
def get_rag(request: Request) -> RAGPipeline:
    return request.app.state.rag

def get_engine(request: Request) -> QueryEngine:
    return request.app.state.engine

def get_curriculum(request: Request) -> CurriculumManager:
    return request.app.state.curriculum

def get_knowledge_state(request: Request) -> KnowledgeStateManager:
    return request.app.state.knowledge_state
```

---

### 4.32 Logging Middleware (logging_middleware.py)

**File:** `backend/app/logging_middleware.py` (10 lines)

```python
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="")

class RequestIDFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_var.get()[:8] or "-"
        return True
```

Used in `server.py` to inject `request_id` into every log record via custom `LogRecordFactory`.

---

### 4.33 Schemas (schemas.py)

**File:** `backend/app/schemas.py` (98 lines)

Pydantic v2 models for API request/response validation.

| Model | Fields | Endpoint |
|-------|--------|----------|
| `QueryRequest` | question, course_code, session_id, top_k, language, mastery, bloom_level, image_ids | `/query`, `/query-stream` |
| `QueryResponse` | response, cited_sources, chunks_retrieved, text_chunks, image_chunks | `/query` |
| `ChunkItem` | chunk_id, text, source_title, page, content_type, score | `/chunks` |
| `PaperRequest` | course_code, total_marks, difficulty, topics, top_k, bloom_levels | `/generate-paper` |
| `CourseCreate` | course_code, course_name, description, icon | `POST /courses` |
| `CourseUpdate` | course_name?, description?, icon? | `PUT /courses/{code}` |
| `FlashcardRequest` | course_code, topic, count, bloom_levels? | `POST /flashcards` |
| `SaveFlashcardRequest` | course_code, topic, cards | `POST /flashcards/save` |
| `QuizRequest` | course_code, topic, count, bloom_levels? | `POST /quiz` |
| `SaveQuizRequest` | course_code, topic, questions, score, total, bloom_levels? | `POST /quiz/save` |
| `ChatFeedbackRequest` | question, course_code, helpful | `POST /chat/feedback` |

All string fields constrained by validation constants from `validation.py` (e.g., `MAX_QUESTION_LENGTH=1000`).

---

### 4.34 Router: auth.py

**File:** `backend/app/routers/auth.py`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `POST` | `/auth/register` | Public | Register user. Body: `{email, password, role}`. Returns JWT. |
| `POST` | `/auth/login` | Public | Login with form-encoded `username` (email) + `password`. Returns JWT. |

Login uses `OAuth2PasswordRequestForm` — form-encoded, not JSON. Response: `{access_token, token_type, role}`.

---

### 4.35 Router: query.py

**File:** `backend/app/routers/query.py` (283 lines)

The central Q&A router. Has both **direct SSE** and **async Celery** query paths.

#### Helper: `_load_images(image_ids)` (lines 29-44)
Loads and base64-encodes uploaded images for vision LLM. Path traversal protection: validates resolved path starts with `UPLOAD_DIR`. Supports JPEG/PNG only. Returns list of `{b64, mime}` dicts.

#### Route Table

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `GET` | `/health` | Public | Health check. Returns `{status, version, dependencies: {surrealdb, gemini}}`. |
| `POST` | `/query-async` | JWT | **Async**: kicks off Celery `process_query_task.delay()`, returns `{task_id}` immediately. |
| `GET` | `/query-stream/{task_id}` | JWT | **Async poll**: GET SSE from Redis list via LRANGE. Polls every 200ms. Terminates on `done`/`error`. |
| `POST` | `/query-stream` | JWT | **Direct SSE**: runs full RAG pipeline inline, streams via `StreamingResponse`. Supports image_ids. |
| `POST` | `/query` | JWT | **Non-streaming**: returns complete response. |
| `POST` | `/chat/feedback` | JWT | Submit helpfulness feedback. Updates knowledge state via `ks.update_state()`. |
| `GET` | `/stats` | JWT | Course statistics: document list, chunk counts per course. |
| `GET` | `/chunks` | JWT | Debug chunk retrieval: raw chunks via hybrid search with scores. |

#### SSE Formats

**Direct path (POST /query-stream):**
```
data: {"type": "thinking", "content": "I'll explain..."}
data: {"type": "content", "content": "A modulo-6 counter..."}
data: {"type": "content", "content": " has 6 states..."}
data: {"type": "metadata", "verified": true, "cited_sources": [...], "chunks_retrieved": 10, ...}
```
Events: `thinking` (strategy), `content` (streaming tokens), `metadata` (verification + citations).
On completion: persists `query_log` record + both `user`/`assistant` chat messages.

**Async path (GET /query-stream/{task_id}):**
Same SSE event types, but streamed via Redis list `query_progress:{task_id}`. Frontend polls via `fetch()` with `ReadableStream` reader. Terminates when `{"type": "done"}` or `{"type": "error"}` is received. TTL 600s on Redis key.

| Detail | Direct SSE | Async Celery |
|--------|-----------|-------------|
| Latency perception | Instant (no spinner) | task_id → polling delay |
| HTTP timeout risk | Yes (long-lived connection) | No (two short requests) |
| Worker crash recovery | None | Frontend retries from `sessionStorage` |
| Scalability | Tied to FastAPI workers | Independent Celery workers |

---

### 4.36 Router: courses.py

**File:** `backend/app/routers/courses.py`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `GET` | `/courses` | JWT | List all courses with batch stats (chunk counts). |
| `POST` | `/courses` | JWT+faculty | Create course. Body: `{course_code, course_name, description, icon}`. |
| `GET` | `/courses/{code}` | JWT | Get single course with full stats. |
| `PUT` | `/courses/{code}` | JWT+faculty | Update course (partial). |
| `DELETE` | `/courses/{code}` | JWT+faculty | Delete course + cascade delete all related data. |
| `GET` | `/curriculum` | JWT | List curriculum files for a course. Query: `course`. |
| `GET` | `/curriculum/topics` | JWT | Get curriculum topics for a course. Query: `course`. |
| `GET` | `/courses/{code}/topics` | JWT | Get structured topics with subtopics, prerequisites, Bloom levels. |
| `GET` | `/courses/{code}/coverage` | JWT | Get topic coverage (covered/missing per topic). |

---

### 4.37 Router: ingestion.py

**File:** `backend/app/routers/ingestion.py`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `POST` | `/ingest` | JWT+faculty | Ingest PDF as course material. Multipart: `file`, `course_code`, `topic`. Returns chunk counts. |
| `POST` | `/curriculum` | JWT+faculty | Upload curriculum PDF. Multipart: `file`, `course_code`. Triggers topic extraction. |
| `DELETE` | `/materials/{code}` | JWT+faculty | Delete ingested material by filename. Query: `filename`. |
| `DELETE` | `/curriculum/{code}` | JWT+faculty | Delete curriculum document by filename. Query: `filename`. |

Ingestion runs blocking inline (not async background) unless configured for Celery.

> **LaTeX TikZ — Ingestion Pipeline:**
> ```latex
> \documentclass[tikz,border=10pt]{standalone}
> \usepackage{tikz}
> \usetikzlibrary{positioning,arrows.meta}
> \begin{document}
> \begin{tikzpicture}[
>   node distance=1cm and 2cm,
>   step/.style={rectangle, draw, rounded corners, minimum width=2.8cm, minimum height=0.8cm, align=center, font=\small\sffamily},
>   arrow/.style={-{Latex[length=2mm]}, thick}
> ]
> \node[font=\Large\bfseries\sffamily] at (0,6.5) {PDF Ingestion Pipeline};
> \node[step] (upload) at (0,5) {Multipart Upload};
> \node[step, fill=gray!10] (hash) at (0,3.5) {SHA-256 Duplicate Check};
> \node[step, fill=green!10] (extract) at (0,2) {PyPDF Extraction};
> \node[step, fill=blue!10] (text) at (-2.5,0) {Text: clean/chunk/embed};
> \node[step, fill=blue!10] (img) at (2.5,0) {Image: validate/embed};
> \node[step, fill=orange!10] (record) at (0,-2) {Record in document table};
> \node[step] (ret) at (0,-3.5) {Return chunk counts};
> \draw[arrow] (upload) -- (hash);
> \draw[arrow] (hash) -- node[right,font=\small\sffamily] {new} (extract);
> \draw[arrow] (extract) -- (text);
> \draw[arrow] (extract) -- (img);
> \draw[arrow] (text) -- (record);
> \draw[arrow] (img) -- (record);
> \draw[arrow] (record) -- (ret);
> \end{tikzpicture}
> \end{document}
> ```

---

### 4.38 Router: chat.py

**File:** `backend/app/routers/chat.py`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `GET` | `/chat-history` | JWT | Get chat history. Query: `course_code`, `session_id`. |
| `POST` | `/chat-history` | JWT | Save a message. Query: `course_code`, `session_id`, `role`, `content`. |
| `DELETE` | `/chat-history` | JWT | Clear history. Query: `course_code`, `session_id`. |

---

### 4.39 Router: flashcards.py

**File:** `backend/app/routers/flashcards.py`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `POST` | `/flashcards` | JWT | Generate flashcards via LLM. Body: `{course_code, topic, count, bloom_levels?}`. |
| `POST` | `/flashcards/save` | JWT | Save flashcard set to DB. Body: `{course_code, topic, cards}`. |
| `GET` | `/flashcards/saved` | JWT | List saved sets. Query: `course_code`. |
| `DELETE` | `/flashcards/saved/{id}` | JWT | Delete set (owner only). |

---

### 4.40 Router: quiz.py

**File:** `backend/app/routers/quiz.py`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `POST` | `/quiz` | JWT | Generate quiz via LLM. Body: `{course_code, topic, count, bloom_levels?}`. |
| `POST` | `/quiz/save` | JWT | Save quiz result, updates knowledge state. Body: `{course_code, topic, questions, score, total}`. |
| `GET` | `/quiz/saved` | JWT | List saved quizzes. Query: `course_code`. |
| `DELETE` | `/quiz/saved/{id}` | JWT | Delete quiz (owner only). |

Saving a quiz triggers `knowledge_state.update_state()` for each question, which updates mastery and logs to `question_log`.

---

### 4.41 Router: analytics.py

**File:** `backend/app/routers/analytics.py`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `GET` | `/analytics/me` | JWT+student | Current user's analytics: top questions, weak topics, Bloom mastery, activity. |
| `GET` | `/analytics` | JWT+faculty | Course-wide analytics: top questions, weak topics, coverage. |
| `GET` | `/analytics/unanswered` | JWT+faculty | Out-of-scope/unanswered questions. |
| `GET` | `/analytics/coverage` | JWT+faculty | Topic coverage metrics. |
| `GET` | `/questions` | JWT+faculty | All questions asked for a course. |
| `GET` | `/analytics/gaps` | JWT+student | Knowledge gap detection for current user. |

---

### 4.42 Router: paper.py

**File:** `backend/app/routers/paper.py`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `POST` | `/generate-paper` | JWT+faculty | Generate exam paper. Body: `{course_code, total_marks, difficulty, topics, top_k, bloom_levels?}`. |

---

### 4.43 Router: images.py

**File:** `backend/app/routers/images.py`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `POST` | `/chat-images` | JWT | Upload image for chat. Multipart: `file` (JPEG/PNG, max 5MB). Returns session_id + filename. |
| `GET` | `/chat-images/{session_id}/{file_name}` | Public | Retrieve uploaded image. |

Images stored on filesystem at `./chat_images/{session_id}/{filename}`.

---

### 4.44 Router: admin.py

**File:** `backend/app/routers/admin.py`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `GET` | `/admin/users` | JWT+admin | List all users. |
| `GET` | `/admin/stats` | JWT+admin | Platform stats: total users, courses, documents, conversations. |

---

### 4.45 Router: users.py

**File:** `backend/app/routers/users.py`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `GET` | `/users/me` | JWT | Get current user profile. |
| `PUT` | `/users/me` | JWT | Update current user's name. Body: `{name}`. |

---

### 4.46 Router: learning_path.py

**File:** `backend/app/routers/learning_path.py`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `GET` | `/api/learning-paths/{course_code}/next` | JWT+student | Get recommended next topics (ZPD candidates). |

---

### 4.47 Router: tasks.py

**File:** `backend/app/routers/tasks.py`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `GET` | `/tasks/{task_id}` | JWT | Get Celery task status. |
| `DELETE` | `/tasks/{task_id}` | JWT | Revoke running task. |
| `POST` | `/scheduler/run` | JWT+admin | Manually trigger nightly scheduler. |

---

## 5. Database Schema

**Database:** SurrealDB, namespace `adaptive_learning`, database `learning_platform`.

### Tables

#### `text_chunk` — Document text chunks
| Field | Type | | Field | Type |
|-------|------|------|-------|------|
| `course_code` | `string` | | `source_title` | `string` |
| `topic` | `string` | | `page` | `number` |
| `text` | `string` | | `embedding` | `array<float>` |
| `content_type` | `string` | | (id auto-generated) | |
**Indexes:** `text_search_idx` (BM25 fulltext on `text`), `text_embedding_idx` (HNSW cosine on `embedding`), `text_chunk_course_idx` (on `course_code`)

#### `image_chunk` — Extracted diagram images
| Field | Type | | Field | Type |
|-------|------|------|-------|------|
| `course_code` | `string` | | `source_title` | `string` |
| `topic` | `string` | | `page` | `number` |
| `text` | `string` | | `embedding` | `array<float>` |
| `content_type` | `string` | | `mime_type` | `string` |
| `image_size_kb` | `number` | | | |
**Indexes:** `image_embedding_idx` (HNSW cosine on `embedding`), `image_chunk_course_idx` (on `course_code`)

#### `curriculum_chunk` — Syllabus/curriculum content
| Field | Type | | Field | Type |
|-------|------|------|-------|------|
| `course_code` | `string` | | `source_title` | `string` |
| `topic` | `string` | | `page` | `number` |
| `text` | `string` | | `embedding` | `array<float>` |
| `content_type` | `string` | | | |
**Indexes:** `curriculum_embedding_idx` (HNSW cosine on `embedding`), `curriculum_chunk_course_idx` (on `course_code`)

#### `course` — Course metadata
| Field | Type | | Field | Type |
|-------|------|------|-------|------|
| `course_code` | `string` (unique) | | `course_name` | `string` |
| `description` | `string` | | `icon` | `string` |
| `created_at` | `datetime (DEFAULT time::now())` | | | |
**Index:** `course_code_idx` (unique on `course_code`)
**Event:** `course_cascade_delete` — on DELETE, removes all related chunks, topics, states

#### `course_topic` — Structured topics from syllabus
| Field | Type | | Field | Type |
|-------|------|------|-------|------|
| `course_code` | `string` | | `topic_name` | `string` |
| `subtopics` | `array<string>` | | `prerequisites` | `array<string>` |
| `bloom_level` | `option<string>` | | `learning_objectives` | `array<string>` |
| `order_index` | `number` | | | |
**Index:** `ct_course_topic_idx` (unique on `course_code, topic_name`)

#### `document` — Ingested document deduplication
| Field | Type | | Field | Type |
|-------|------|------|-------|------|
| `course_code` | `string` | | `filename` | `string` |
| `content_hash` | `string` | | `doc_type` | `string` (material/curriculum) |
| `created_at` | `string` | | | |
**Index:** `document_hash_idx` (unique on `course_code, content_hash`)

#### `user` — Auth users
| Field | Type | | Field | Type |
|-------|------|------|-------|------|
| `user_id` | `string` (unique) | | `email` | `string` (unique) |
| `hashed_password` | `string` | | `role` | `string` (student/faculty/admin) |
| `name` | `string` | | `created_at` | `datetime (DEFAULT time::now())` |
**Indexes:** `user_email_idx` (unique on `email`), `user_user_id_idx` (unique on `user_id`)

#### `chat_message` — Conversation history
| Field | Type | | Field | Type |
|-------|------|------|-------|------|
| `user_id` | `string` | | `course_code` | `string` |
| `session_id` | `string` | | `message_role` | `string` (user/assistant) |
| `content` | `string` | | `timestamp` | `datetime (DEFAULT time::now())` |
**Index:** `chat_course_session_idx` (on `course_code, session_id`)

#### `query_log` — Analytics: every query
| Field | Type | | Field | Type |
|-------|------|------|-------|------|
| `user_id` | `string` | | `course_code` | `string` |
| `question` | `string` | | `response_preview` | `string` |
| `out_of_scope` | `option<bool> (DEFAULT false)` | | `cited_sources` | `array<object>` |
| `timestamp` | `datetime (DEFAULT time::now())` | | | |
- `cited_sources[*].source_title` — `string`
- `cited_sources[*].page` — `string`
- `cited_sources[*].content_type` — `string`
- `cited_sources[*].has_image` — `bool`
**Index:** `query_log_course_idx` (on `course_code`)

#### `quiz` — Saved quiz attempts
| Field | Type | | Field | Type |
|-------|------|------|-------|------|
| `user_id` | `string` | | `course_code` | `string` |
| `topic` | `string` | | `bloom_levels` | `array` |
| `questions` | `any` | | `score` | `int` |
| `total` | `int` | | `created_at` | `datetime (DEFAULT time::now())` |
| `completed_at` | `datetime` | | | |
**Index:** `quiz_course_idx` (on `course_code`)

#### `flashcard_set` — Saved flashcard sets
| Field | Type | | Field | Type |
|-------|------|------|-------|------|
| `user_id` | `string` | | `course_code` | `string` |
| `topic` | `string` | | `bloom_level` | `int` |
| `cards` | `any` | | `created_at` | `datetime (DEFAULT time::now())` |
**Index:** `flashcard_course_idx` (on `course_code`)

#### `knowledge_state` — Per-student mastery
| Field | Type | | Field | Type |
|-------|------|------|-------|------|
| `student_id` | `string` | | `course_code` | `string` |
| `topic_id` | `string` | | `bloom_level` | `int` |
| `mastery_score` | `float` | | `confidence` | `float` |
| `stability` | `option<float>` | | `difficulty` | `option<float>` |
| `total_attempts` | `int` | | `correct_attempts` | `int` |
| `streak` | `int` | | `last_reviewed_at` | `option<datetime>` |
| `next_review_at` | `option<datetime>` | | `updated_at` | `datetime (DEFAULT time::now())` |
**Index:** `ks_student_course` (unique on `student_id, course_code, topic_id, bloom_level`)

#### `topic_prerequisite` — Prerequisite DAG edges
| Field | Type | | Field | Type |
|-------|------|------|-------|------|
| `course_code` | `string` | | `topic_from` | `string` |
| `topic_to` | `string` | | `prereq_type` | `string` (hard/sequential) |
**Index:** `tp_course_idx` (on `course_code`)

#### `question_log` — Individual question correctness records
| Field | Type | | Field | Type |
|-------|------|------|-------|------|
| `student_id` | `string` | | `course_code` | `string` |
| `topic_id` | `string` | | `bloom_level` | `int` |
| `question_text` | `option<string>` | | `is_correct` | `bool` |
| `source` | `string` (quiz/flashcard/feedback) | | `timestamp` | `datetime (DEFAULT time::now())` |
**Index:** `ql_student_course_idx` (on `student_id, course_code`)

> **LaTeX TikZ — Database Schema (14 tables):**
> ```latex
> \documentclass[tikz,border=10pt]{standalone}
> \usepackage{tikz}
> \usetikzlibrary{positioning,arrows.meta}
> \begin{document}
> \begin{tikzpicture}[
>   node distance=1.8cm,
>   tbl/.style={rectangle, draw, rounded corners=2pt, minimum width=5cm, align=left, font=\footnotesize\ttfamily, inner sep=4pt},
>   tbltitle/.style={tbl, fill=blue!10, font=\small\bfseries\ttfamily}
> ]
> \node[font=\Large\bfseries\sffamily] at (0,9) {Database Schema --- SurrealDB (14 tables)};
> \node[font=\small\sffamily] at (0,8.2) {Namespace: adaptive\_learning / DB: learning\_platform};
> \node[tbltitle] (user) at (-6.5,6) {user};
> \node[tbl, below=0pt of user] {user\_id / email (unique)\\hashed\_password / role\\name / created\_at};
> \node[tbltitle] (course) at (0,6) {course};
> \node[tbl, below=0pt of course] {course\_code (unique) / course\_name\\description / icon / created\_at\\Event: cascade delete};
> \node[tbltitle] (doc) at (6.5,6) {document};
> \node[tbl, below=0pt of doc] {course\_code / filename\\content\_hash (unique) / doc\_type};
> \node[tbltitle] (tc) at (-6.5,2.5) {text\_chunk (HNSW+BM25)};
> \node[tbl, below=0pt of tc] {course\_code / source\_title / page\\text / embedding / content\_type};
> \node[tbltitle] (ic) at (0,2.5) {image\_chunk (HNSW)};
> \node[tbl, below=0pt of ic] {course\_code / source\_title / page\\text / embedding / mime\_type};
> \node[tbltitle] (cc) at (6.5,2.5) {curriculum\_chunk (HNSW)};
> \node[tbl, below=0pt of cc] {course\_code / source\_title / page\\text / embedding};
> \node[tbltitle] (ct) at (-6.5,-0.5) {course\_topic};
> \node[tbl, below=0pt of ct] {course\_code / topic\_name\\subtopics / prerequisites / bloom\_level};
> \node[tbltitle] (ch) at (0,-0.5) {chat\_message};
> \node[tbl, below=0pt of ch] {user\_id / course\_code\\session\_id / message\_role / content};
> \node[tbltitle] (ql) at (6.5,-0.5) {query\_log};
> \node[tbl, below=0pt of ql] {user\_id / course\_code\\question / cited\_sources / out\_of\_scope};
> \node[tbltitle] (ks) at (-6.5,-3.5) {knowledge\_state};
> \node[tbl, below=0pt of ks] {student\_id / course\_code / topic\_id\\bloom\_level / mastery\_score\\confidence / attempts / streak};
> \node[tbltitle] (qg) at (0,-3.5) {question\_log};
> \node[tbl, below=0pt of qg] {student\_id / course\_code\\topic\_id / bloom\_level / is\_correct};
> \node[tbltitle] (tp) at (6.5,-3.5) {topic\_prerequisite};
> \node[tbl, below=0pt of tp] {course\_code / topic\_from\\topic\_to / prereq\_type};
> \end{tikzpicture}
> \end{document}
> ```

---

## 6. Frontend Implementation

### 6.1 Package Dependencies

**Runtime (10):**
- `next` 16.2.9 — React framework (App Router)
- `react` 19.2.4, `react-dom` 19.2.4
- `@tanstack/react-query` 5.101.2 — Server state management
- `zustand` 5.0.14 — Client state (auth store)
- `axios` 1.18.1 — HTTP client
- `lucide-react` 1.21.0 — Icon library
- `react-markdown` 10.1.0 + `rehype-raw` 7.0.0 + `remark-gfm` 4.0.1 — Markdown rendering for AI responses

**Dev (7):**
- `@playwright/test` 1.61.1 — E2E testing
- `typescript` 6.0.3
- `eslint` 9 + `eslint-config-next` 16.2.9
- `@types/node`, `@types/react`, `@types/react-dom`

### 6.2 Next.js Configuration

**File:** `new_frontend/next.config.mjs`

```javascript
const BACKEND = process.env.API_PROXY_TARGET || 'http://localhost:8001';
const nextConfig = {
  output: 'standalone',
  typescript: { ignoreBuildErrors: true },
  rewrites: async () => [
    { source: '/auth/:path*', destination: `${BACKEND}/auth/:path*` },
    { source: '/query/:path*', destination: `${BACKEND}/query/:path*` },
    { source: '/query-async', destination: `${BACKEND}/query-async` },
    { source: '/query-stream/:path*', destination: `${BACKEND}/query-stream/:path*` },
    // ... 24 more rewrite rules ...
    { source: '/stats', destination: `${BACKEND}/stats` },
  ],
};

**Key decisions:**
- `output: 'standalone'` — Docker-optimized output
- `ignoreBuildErrors: true` — TS errors don't block deployment
- 28 rewrite rules proxy all API calls to backend — no CORS needed since all traffic goes through Next.js

### 6.3 TypeScript Configuration

**File:** `new_frontend/tsconfig.json`

```json
{
  "compilerOptions": {
    "strict": false,
    "target": "ES2017",
    "module": "esnext",
    "moduleResolution": "bundler",
    "paths": { "@/*": ["./src/*"] },
    // ... standard Next.js settings
  }
}
```

**Key:** `strict: false` — loose type checking, `@/*` path alias to `src/`.

### 6.4 API Client Layer

**File:** `new_frontend/src/lib/api/client.ts`

```typescript
export const api = axios.create({
  baseURL: '',       // relies on Next.js rewrites
  timeout: 60_000,
});

// Request interceptor: attach Bearer token
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Response interceptor: auto-logout on 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) useAuthStore.getState().logout();
    return Promise.reject(err);
  }
);
```

**All API modules** (`src/lib/api/*.ts`) import this `api` instance and define typed functions for each endpoint.

### 6.5 Auth Store

**File:** `new_frontend/src/lib/store/authStore.ts`

Zustand store persisted to `localStorage` under key `uniauth`:

```typescript
interface AuthState {
  token: string | null;
  user: { email: string; role: string; name?: string } | null;
  isAuthenticated: boolean;

  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}
```

- **`login()`** — calls `authApi.login()` with form-encoded data, stores token + user + role
- **`logout()`** — clears state, redirects to `/`

Persistence: zustand `persist` middleware writes to `localStorage('uniauth')`.

### 6.6 Pages & Layouts

| Route | File | Description |
|-------|------|-------------|
| `/` | `src/app/page.tsx` | **Login** — "Vbook LM / University AI Platform" branding, role tabs (Student/Faculty/Admin), client-side email validation via `validateEmail()`, `?redirect=` param support in both auto-redirect (useEffect) and login flow, password visibility toggle |
| `/register` | `src/app/register/page.tsx` | **Register** — email, password, role selector |
| `/student/dashboard` | `src/app/student/dashboard/page.tsx` | Course cards, radial progress, stats tiles |
| `/student/courses/[code]` | `src/app/student/courses/[code]/page.tsx` | **AI study assistant** — async Celery-based query flow: `handleSend()` calls `submitQueryAsync()` → Celery task, `attachStream()` polls via `queryStreamTask()` (GET SSE), `resumeActiveTask()` + `useEffect` recovers in-flight queries from `sessionStorage`. `ChatMessage` (React.memo) renders verified/unverified banners, source chips, thinking block (collapsible `<details>`), Copy/Helpful buttons. `cite()` wraps `[Source:...]` in `<cite>` tags, strips other HTML. `react-markdown` with `remark-gfm` + `rehype-raw` (dynamic import, ssr: false). Bloom's level dropdown, image upload preview (max 5), abort controller on unmount, loading skeleton |
| `/student/quiz` | `src/app/student/quiz/page.tsx` | MCQ quiz with course/topic/Bloom's config, timer, results + save |
| `/student/flashcards` | `src/app/student/flashcards/page.tsx` | Flashcard generator + flip study session |
| `/student/progress` | `src/app/student/progress/page.tsx` | Weak topics, study activity, revision suggestions |
| `/student/profile` | `src/app/student/profile/page.tsx` | View/edit name |
| `/faculty/dashboard` | `src/app/faculty/dashboard/page.tsx` | Course list, stat tiles, add course modal |
| `/faculty/analytics` | `src/app/faculty/analytics/page.tsx` | Question volume chart, trending Qs, weak topics, coverage |
| `/faculty/course/[code]` | `src/app/faculty/course/[code]/page.tsx` | Upload materials/curriculum PDFs, topic extraction display |
| `/faculty/generate` | `src/app/faculty/generate/page.tsx` | Question paper generator with Bloom's config + preview |
| `/faculty/profile` | `src/app/faculty/profile/page.tsx` | View/edit name |
| `/admin/dashboard` | `src/app/admin/dashboard/page.tsx` | Platform stats (users/courses/docs/conversations), user table |
| `/admin/profile` | `src/app/admin/profile/page.tsx` | View/edit name |

**Layouts:**
- `root` (`layout.tsx`) — wraps in `<Providers>` (React Query + Toast), sets Inter + JetBrains Mono fonts
- `student/layout.tsx` — auth guard with `<Suspense>` wrapper; redirects with `?redirect=` param on role mismatch
- `admin/layout.tsx`, `faculty/layout.tsx` — auth guards: redirect to `/?redirect=<path>` on unauthenticated access, redirect to correct role dashboard on role mismatch

### 6.7 Components

**Shell & Navigation:**
| Component | Purpose |
|-----------|---------|
| `AppShell` | Main layout: Sidebar + TopBar + content area. Props for navRole, activeKey, topBarVariant |
| `Sidebar` | Role-based nav: Student (Dashboard, Quiz, Flashcards, Progress), Faculty (Dashboard, Analytics), Admin (Dashboard). Logout button |
| `TopBar` | 3 variants: `search` (search pill), `tabs` (page tabs), `breadcrumbBack` (back + breadcrumbs). History/Notifications/Avatar |
| `Breadcrumbs` | Breadcrumb trail with chevron separators |

**Data Display:**
| Component | Purpose |
|-----------|---------|
| `CourseCard` | Course card with title, description, icon, chunk stats |
| `DataTable` | Generic table with column config, empty state, "View All" footer |
| `StatTile` | Metric display tile with label, value, icon |
| `RadialProgress` | Circular progress indicator (SVG-based) |
| `ProgressBar` | Horizontal progress bar |
| `Badge` | Status badge (e.g., "Covered", "Missing") |
| `BloomPill` | Bloom's taxonomy level pill |
| `FileTypeIcon` | File type icon (PDF, image, etc.) |
| `PaperPreview` | Exam paper preview component |

**Forms & Input:**
| Component | Purpose |
|-----------|---------|
| `FormField` | Label + input + error with consistent styling |
| `Dropzone` | File drop zone for PDF uploads |
| `CheckboxCard` | Card-style checkbox for topic selection |
| `RemovableSection` | Section with remove button |

**Overlays:**
| Component | Purpose |
|-----------|---------|
| `Modal` | Accessible modal: Esc to close, focus trap, scroll lock, return focus |
| `Toast` | Toast notification styling |
| `ToastContext` | React context: `showToast(message, type)` — auto-dismiss 3s |
| `AvatarOrInitials` | Avatar with user initials fallback |

> **LaTeX TikZ — Frontend Component Tree:**
> ```latex
> \documentclass[tikz,border=10pt]{standalone}
> \usepackage{tikz}
> \usetikzlibrary{positioning,arrows.meta}
> \begin{document}
> \begin{tikzpicture}[
>   grow=down, level distance=1.2cm, sibling distance=5cm,
>   edge from parent/.style={draw, -{Latex[length=1.5mm]}, thick},
>   node/.style={rectangle, draw, rounded corners, align=center, font=\footnotesize\sffamily, inner sep=3pt},
>   page/.style={node, fill=green!10, minimum width=2.5cm},
>   comp/.style={node, fill=blue!5, minimum width=2cm},
>   layout/.style={node, fill=yellow!10, minimum width=2cm},
>   store/.style={node, fill=purple!10, minimum width=2cm}
> ]
> \node[font=\Large\bfseries\sffamily] at (0,2) {Frontend Component Tree};
> \node[page] (root) at (0,0) {Root Layout};
> \path (root) ++(-1.2,-0.8) node[page] (login) {Login /};
> \path (root) ++(1.2,-0.8) node[page] (reg) {Register};
> \path (root) ++(-5.5,-2) node[layout] (sl) {Student Layout};
> \path (root) ++(0,-2) node[layout] (fl) {Faculty Layout};
> \path (root) ++(5.5,-2) node[layout] (al) {Admin Layout};
> \path (sl) ++(-2.5,-1.2) node[page] (sd) {Dashboard};
> \path (sl) ++(0,-1.2) node[page] (cd) {Course Detail};
> \path (sl) ++(2.5,-1.2) node[page] (qz) {Quiz};
> \path (cd) ++(-2,-1.2) node[comp] (cm) {ChatMessage};
> \path (cd) ++(2,-1.2) node[comp] (rm) {ReactMarkdown};
> \node[comp] (as) at (-8,-3.5) {AppShell};
> \path (as) ++(-1.5,-1.2) node[comp] (sb) {Sidebar};
> \path (as) ++(1.5,-1.2) node[comp] (tb) {TopBar};
> \node[store] at (8,-3.5) {Zustand Auth Store};
> \draw[edge from parent] (root) -- (login);
> \draw[edge from parent] (root) -- (reg);
> \draw[edge from parent] (root) -- (sl);
> \draw[edge from parent] (root) -- (fl);
> \draw[edge from parent] (root) -- (al);
> \draw[edge from parent] (sl) -- (sd);
> \draw[edge from parent] (sl) -- (cd);
> \draw[edge from parent] (sl) -- (qz);
> \draw[edge from parent] (cd) -- (cm);
> \draw[edge from parent] (cd) -- (rm);
> \draw[edge from parent] (sl) -- (as);
> \end{tikzpicture}
> \end{document}
> ```

### 6.8 API Modules

| File | Functions | Endpoints |
|------|-----------|-----------|
| `auth.ts` | `login()`, `register()` | `POST /auth/login`, `POST /auth/register` |
| `courses.ts` | `list()`, `get()`, `create()`, `update()`, `delete()`, `getStats()`, `getTopics()`, `getCoverage()` | CRUD `/courses`, `/stats`, `/courses/{code}/topics`, `/courses/{code}/coverage` |
| `chat.ts` | `submitQueryAsync()` → Celery task, `queryStreamTask()` (GET SSE polling), `queryStream()` (direct POST SSE), `parseUserMessage()` (JSON content parsing), `feedback()`, `getHistory()`, `addMessage()`, `clearHistory()`, `uploadImage()` | `/query-async`, `/query-stream`, `/query-stream/{taskId}`, `/chat/feedback`, `/chat-history`, `/chat-images` |
| `quiz.ts` | `generate()`, `save()`, `listSaved()`, `deleteSaved()` | `/quiz`, `/quiz/save`, `/quiz/saved` |
| `flashcards.ts` | `generate()`, `save()`, `listSaved()`, `deleteSaved()` | `/flashcards`, `/flashcards/save`, `/flashcards/saved` |
| `paper.ts` | `generate()` | `POST /generate-paper` |
| `ingestion.ts` | `ingestPdf()`, `uploadCurriculum()`, `deleteMaterial()`, `deleteCurriculum()` | `/ingest`, `/curriculum`, `/materials/{code}`, `/curriculum/{code}` |
| `analytics.ts` | `getMy()`, `get()`, `getUnanswered()`, `getCoverage()`, `getGaps()` | `/analytics/me`, `/analytics`, `/analytics/unanswered`, `/analytics/coverage`, `/analytics/gaps` |
| `admin.ts` | `listUsers()`, `getStats()` | `GET /admin/users`, `GET /admin/stats` |
| `users.ts` | `getMe()`, `updateMe()` | `GET /users/me`, `PUT /users/me` |
| `types.ts` | 30+ TypeScript interfaces | Request/response types for all APIs |

**Streaming SSE Implementation (chat.ts) — Dual Mode:**

**Async polling (preferred — Celery-based):**
```typescript
// Step 1: Kick off Celery task
const { task_id } = await api.post('/query-async', body);

// Step 2: Poll SSE stream via GET
const response = await fetch(`/query-stream/${task_id}`, {
  headers: { Authorization: `Bearer ${token}` },
});
const reader = response.body.getReader();
const decoder = new TextDecoder();
while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  // Parse SSE data: dispatch to onThinking/onContent/onMetadata/onDone/onError
}
```

**Direct POST SSE (legacy):**
```typescript
const response = await fetch('/query-stream', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
  body: JSON.stringify(body),
});
// Same ReadableStream reader pattern
```

The `queryStreamTask()` function in chat.ts polls the Redis-backed SSE endpoint, parsing each `data:` line into typed events (`thinking`/`content`/`metadata`/`done`/`error`). The `parseUserMessage()` helper handles JSON-encoded user content `{text, images}` from chat history.

### 6.9 CSS Architecture

**No Tailwind CSS.** Uses CSS custom properties + CSS Modules.

**`globals.css`** — Design tokens:
```css
:root {
  --color-primary: #2563eb;
  --color-primary-hover: #1d4ed8;
  --color-bg: #f8fafc;
  --color-surface: #ffffff;
  --color-text: #1e293b;
  --color-text-secondary: #64748b;
  --color-border: #e2e8f0;
  --color-success: #22c55e;
  --color-warning: #f59e0b;
  --color-error: #ef4444;
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.07);
  --font-sans: 'Inter', sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
  /* ... more tokens */
}
```

**Per-page CSS modules** (`page.module.css`): Each page has its own CSS module for scoped styling. Components use the same pattern (`Component.module.css`).

---

## 7. Infrastructure

### 7.1 Docker Compose

**File:** `docker-compose.yml` — 5 services:

```yaml
services:
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  surrealdb:
    image: surrealdb/surrealdb:latest
    command: start --user root --pass root surrealkv://data/surrealdb.db
    ports: ["8000:8000"]
    volumes: [surreal_data:/data]

  backend:
    build: ./backend
    ports: ["8001:8001"]
    environment:
      SURREAL_URL: ws://surrealdb:8000/rpc
      GEMINI_API_KEYS: ${GEMINI_API_KEYS}
      OPENROUTER_API_KEYS: ${OPENROUTER_API_KEYS}
      JWT_SECRET: ${JWT_SECRET}
      # ... more env vars
    depends_on: [surrealdb]
    volumes: [./backend/storage:/app/storage]

  worker:
    build: ./backend
    command: celery -A app.tasks worker --loglevel=info
    environment:
      CELERY_BROKER_URL: redis://redis:6379/0
      # ... same env vars as backend
    depends_on: [redis, surrealdb]

  frontend:
    build:
      context: ./new_frontend
      args: [API_PROXY_TARGET=http://backend:8001]
    ports: ["3000:3000"]
    depends_on: [backend]
```

**Volumes:** `surreal_data` — persists SurrealDB data.

### 7.2 Backend Dockerfile

**File:** `backend/Dockerfile`

```dockerfile
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"
COPY . .
EXPOSE 8001
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
```

Pre-downloads NLTK punkt tokenizer data into the image.

### 7.3 Frontend Dockerfile

**File:** `new_frontend/Dockerfile` — multi-stage build:

```dockerfile
# Stage 1: deps
FROM node:20-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci

# Stage 2: builder
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ARG API_PROXY_TARGET
ENV API_PROXY_TARGET=$API_PROXY_TARGET
RUN npm run build

# Stage 3: runner
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
USER nextjs
EXPOSE 3000
CMD ["node", "server.js"]
```

Uses `standalone` output from Next.js — minimal production image.

### 7.4 Production Deployment (prod.sh)

**File:** `prod.sh` (188 lines)

Full production script that:
1. Installs cloudflared and Caddy if missing
2. Sets up Caddy reverse proxy (port 8080 → backend:8001, frontend:3000)
3. Starts Docker services (surrealdb, redis, backend, worker)
4. Runs frontend natively (not in Docker)
5. Starts Cloudflare Tunnel (trycloudflare.com) for public URL
6. Displays tunnel URL
7. Cleanup on Ctrl+C

---

## 8. Testing

### 8.1 Python Tests

**Directory:** `backend/tests/` — 10 test files

| File | Tests | Lines | Coverage |
|------|-------|-------|----------|
| `test_auth.py` | Password hashing, JWT create/decode/expiry/malformed, role enforcement, user extraction | 17 tests | auth.py |
| `test_db_logic.py` | SurrealDB connection, schema init, course CRUD, chat history, curriculum, knowledge state, gap detection, topic coverage | Multiple | db.py, courses.py, knowledge_state.py, gap_detection.py |
| `test_rag.py` | Chunking, citation functions, system prompts, context window, RAGPipeline methods (ingest, retrieve, stats) | Multiple | chunker.py, citation.py, query_engine.py, rag.py |
| `test_e2e_pipeline.py` | Full ingest→retrieve→generate→validate pipeline | 4 tests (skipped) | Full pipeline |
| `test_api_limits.py` | Upload size limit middleware (413 on oversized) | 3 tests | server.py |
| `test_validation.py` | sanitize_id, validate_id edge cases | 8 tests | validation.py |
| `test_validation_extended.py` | sanitize_student_query injection patterns, validate_course_code, sanitize_text, validate_filename | Multiple | validation.py |
| `test_scheduler.py` | _mastery_to_rating boundary values, _schedule_simple ratings/streaks | Multiple | scheduler.py |

**Test Configuration (`conftest.py`):**
- Overrides `SURREAL_NS` to `test_ns`, `SURREAL_DB` to `test_db`
- `surreal_db` fixture: resets singleton, deletes all tables, re-inits schema before each test
- Requires a running SurrealDB instance

**Running tests:**
```bash
# All tests (needs SurrealDB)
cd backend && pytest tests/ -v

# Unit tests only (no DB)
cd backend && pytest tests/test_auth.py -v
```

### 8.2 Playwright E2E Tests

**File:** `new_frontend/playwright.config.ts`

**6 Projects:**
| Project | Auth State | Matches |
|---------|-----------|---------|
| `noauth` | None | `auth*.spec.ts` |
| `student` | `.auth/student.json` | `student*.spec.ts` |
| `faculty` | `.auth/faculty.json` | `faculty*.spec.ts` |
| `admin` | `.auth/admin.json` | `admin*.spec.ts` |
| `diagnose-student` | `.auth/student.json` | `diagnose*` |
| `diagnose-faculty` | `.auth/faculty.json` | `diagnose*` |

**Global Setup (`e2e/global-setup.ts`):**
Registers 3 Playwright users (student/faculty/admin), saves localStorage auth tokens to `.auth/*.json` files.

**Running E2E tests:**
```bash
cd new_frontend && npx playwright test
```

---

## 9. Configuration Reference

### Environment Variables

#### Database
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SURREAL_URL` | No | `ws://localhost:8000/rpc` | SurrealDB WebSocket endpoint |
| `SURREAL_NS` | No | `adaptive_learning` | SurrealDB namespace |
| `SURREAL_DB` | No | `learning_platform` | SurrealDB database name |
| `SURREAL_USER` | No | `root` | SurrealDB auth user |
| `SURREAL_PASS` | No | `root` | SurrealDB auth password |

#### LLM — Chat (Gemini)
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEYS` | Recommended | — | Comma-separated Gemini API keys |
| `GEMINI_API_KEY` | Fallback | — | Single key fallback |
| `GEMINI_MODEL` | No | `gemma-4-31b-it` | Chat model name |
| `GEMINI_VISION_MODEL` | No | `gemma-4-31b-it` | Vision model for image inputs |
| `GEMINI_BASE_URL` | No | `https://generativelanguage.googleapis.com/v1beta/openai` | OpenAI-compatible base URL |

#### LLM — Embeddings (OpenRouter)
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEYS` | Recommended | — | Comma-separated OpenRouter keys |
| `OPENROUTER_API_KEY` | Fallback | — | Single key fallback |
| `OPENROUTER_BASE_URL` | No | `https://openrouter.ai/api/v1` | OpenRouter API base |
| `EMBEDDING_MODEL` | No | `nvidia/llama-nemotron-embed-vl-1b-v2:free` | Embedding model |
| `LLM_MODEL` | No | `gemini-3.6-flash` | Legacy chat model (overridden by GEMINI_MODEL) |
| `TOPIC_EXTRACTION_MODEL` | No | `google/gemma-4-26b-a4b-it:free` | Model for syllabus topic extraction |
| `QUIZ_MODEL` | No | `google/gemma-4-26b-a4b-it:free` | Model for quiz generation |

#### Auth
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JWT_SECRET` | **Yes** | `""` | JWT signing key (⚠️ currently placeholder) |
| `JWT_ALGORITHM` | No | `HS256` | JWT signing algorithm |
| `JWT_EXPIRE_MINUTES` | No | `1440` | Token expiry in minutes (24h) |

#### RAG
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `RAG_TOP_K` | No | `5` | Chunks to retrieve per query |
| `CHUNK_SIZE` | No | `512` | Tokens per chunk |
| `CHUNK_OVERLAP_TOKENS` | No | `64` | Overlap between adjacent chunks |
| `IMAGE_MAX_BATCH_SIZE` | No | `5` | Images per embedding batch |
| `IMAGE_MAX_PER_PDF` | No | `50` | Max images extracted per PDF |
| `RRF_K` | No | `60` | RRF fusion constant |
| `HNSW_EF_SEARCH` | No | `40` | HNSW search breadth |
| `MAX_HISTORY_TURNS` | No | `8` | Recent conversation turns |
| `RAG_MIN_SIMILARITY` | No | `0.4` | Minimum cosine similarity for retrieval |
| `GATEKEEPER_ENABLED` | No | `false` | Enable relevance gatekeeper |
| `QUERY_ENHANCER_ENABLED` | No | `true` | Enable query expansion |
| `QUERY_ENHANCER_NUM_QUERIES` | No | `3` | Number of expanded queries |
| `CORS_ORIGINS` | No | `http://localhost:3000` | CORS allowed origins |

#### Curriculum
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CURRICULUM_K` | No | `3` | Curriculum HNSW top-K |
| `CURRICULUM_EF` | No | `40` | Curriculum HNSW ef |
| `CURRICULUM_THRESHOLD` | No | `0.6` | Curriculum match threshold |

#### Knowledge Tracing
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DKT_ACTIVE` | No | `false` | Deep Knowledge Tracing toggle |
| `MASTERY_THRESHOLD` | No | `0.7` | Mastery cutoff for ZPD |
| `BKT_LEARNING_RATE` | No | `0.15` | BKT learn rate |
| `BKT_P_INIT` | No | `0.15` | BKT initial probability |
| `BKT_P_LEARN` | No | `0.15` | BKT transition prob |
| `BKT_P_GUESS` | No | `0.15` | BKT guess prob |
| `BKT_P_SLIP` | No | `0.10` | BKT slip prob |

---

## 10. RAG Pipeline Data Flow

### Streaming Query (SSE) — Full Path

```
Step 1: Client sends POST /query-stream
        Body: {question, course_code, session_id, top_k, language, mastery, bloom_level, image_ids}

Step 2: Auth middleware validates JWT
        → request.state.user set

Step 3: QueryEngine.query_stream():
  ├── 3a: get_course_context() — queries SurrealDB for course info, documents, curriculum
  │
  ├── 3b: Gatekeeper.check_and_enrich()
  │     LLM call #1: check if query is relevant to course materials
  │     → returns (is_relevant, enriched_query, refusal)
  │     If GATEKEEPER_ENABLED and not relevant: return refusal (no LLM cost)
  │
  ├── 3c: QueryEnhancer.generate_search_queries()
  │     LLM call #2: generate 3 diverse search queries
  │     → returns [query_1, query_2, query_3]
  │
  ├── 3d: For each search query → RAGPipeline.retrieve()
  │     ├── OpenRouter embed_text() — ~100ms
  │     ├── HNSW vector search on text_chunk — ~50ms
  │     ├── HNSW vector search on curriculum_chunk — ~50ms
  │     ├── RRF fusion — ~5ms
  │     └── Dedup by chunk_id, cap at top_k*2 (10)
  │     → returns [{chunk_id, text, source_title, page, similarity, ...}]
  │
  ├── 3e: Build context window
  │     ├── Format chunks as <Text/Curriculum N: Title, Slide/Page N>
  │     ├── Build valid citations list
  │     └── Include last 8 conversation turns
  │
  ├── 3f: Strategy generation
  │     LLM call #3: "Briefly outline your strategy..."
  │     → yields {"type": "thinking", "content": "..."}
  │
  ├── 3g: Streaming response
  │     LLM call #4: Gemini chat completion (streaming)
  │     → yields {"type": "content", "content": "..."} per token
  │
  ├── 3h: Verifier.verify_answer()
  │     LLM call #5: check if answer is grounded in chunks
  │     → (is_valid, reason)
  │     If invalid: yield warning
  │
  └── 3i: Citation extraction
        regex match [Source: ...] in response
        → yields {"type": "metadata", "cited_sources": [...], "verified": ...}

Step 4: Log query to query_log table

Step 5: Client renders streaming response with markdown + source citations
```

### Non-Streaming Query — Same Pipeline + Post-Processing

Additional after streaming:
- `validate_citations()` — if <80% of citations are valid, call `remove_uncited_claims()`
- `remove_uncited_claims()` — NLTK sentence-tokenize, remove uncited claims

### Ingestion Flow

```
Upload PDF → POST /ingest (multipart)
  → Save to temp file
  → RAGPipeline.ingest_pdf():
    ├── SHA-256 hash → check document table for duplicates
    ├── PyPDF text extraction (per page)
    ├── PyPDF image extraction (per page, magic byte validation)
    ├── Text: clean_text() → chunk_text() (512 tokens, 64 overlap)
    ├── Text: OpenRouter embed_text_batch() → insert into text_chunk
    ├── Images: OpenRouter embed_images() (batched, max 5) → insert into image_chunk
    └── Record hash in document table
  → Return {text_chunks, image_chunks, total_chunks}
```

### Timing Estimates

| Operation | Time |
|-----------|------|
| Embedding (single text) | ~100ms |
| Embedding (batch 10) | ~300ms |
| Embedding (image batch 5) | ~1-3s |
| HNSW search (k=5, ef=40) | ~50ms |
| LLM call (gatekeeper) | ~1-2s |
| LLM call (query enhancer) | ~1-2s |
| LLM call (strategy) | ~500ms |
| LLM call (streaming answer) | ~2-5s |
| LLM call (verifier) | ~1-2s |
| PDF ingestion (15MB, 50 pages) | ~20-40s |

**Typical streaming query:** ~5-10s total (3-5 LLM calls)

> **LaTeX TikZ — Query Path Comparison (Direct vs Async):**
> ```latex
> \documentclass[tikz,border=10pt]{standalone}
> \usepackage{tikz}
> \usetikzlibrary{positioning,arrows.meta}
> \begin{document}
> \begin{tikzpicture}[
>   node distance=1cm and 2cm,
>   box/.style={rectangle, draw, rounded corners, minimum width=2.5cm, minimum height=0.8cm, align=center, font=\small\sffamily},
>   arrow/.style={-{Latex[length=2mm]}, thick}
> ]
> \node[font=\Large\bfseries\sffamily] at (0,5) {Query Path Comparison --- Direct vs Async};
> \node[font=\small\bfseries\sffamily] at (-4,4) {Direct SSE (POST /query-stream)};
> \node[box,fill=green!10] (fb) at (-4,3) {Frontend};
> \node[box,fill=blue!10] (be) at (-4,1.5) {FastAPI};
> \node[box,fill=orange!10] (llm) at (-4,0) {Gemini};
> \node[box,fill=blue!10] (be2) at (-4,-1.5) {FastAPI};
> \draw[arrow] (fb) -- node[right,font=\small\sffamily] {POST+SSE} (be);
> \draw[arrow] (be) -- (llm);
> \draw[arrow] (llm) -- (be2);
> \draw[arrow] (be2) -- (fb);
> \node[font=\small\sffamily] at (-4,-3) {Pros: Real-time\\Cons: HTTP timeout, blocking};
> \node[font=\small\bfseries\sffamily] at (4,4) {Async Celery (POST /query-async)};
> \node[box,fill=green!10] (fb2) at (4,3) {Frontend};
> \node[box,fill=blue!10] (be_a) at (4,1.5) {FastAPI};
> \node[box,fill=yellow!10] (cel) at (4,0) {Celery};
> \node[box,fill=orange!10] (llm2) at (4,-1.5) {Gemini};
> \node[box,fill=red!10] (rd) at (4,-3) {Redis};
> \draw[arrow] (fb2) -- node[right,font=\small\sffamily] {POST$\to$task\_id} (be_a);
> \draw[arrow] (be_a) -- (cel);
> \draw[arrow] (cel) -- (llm2);
> \draw[arrow] (llm2) -- (rd);
> \draw[arrow] (fb2) to[bend right=45] node[right,font=\small\sffamily] {GET SSE} (4,-4.5);
> \draw[arrow] (4,-4.5) to[bend right=45] (rd);
> \node[font=\small\sffamily] at (4,-5.5) {Pros: No timeout, resilient\\Scale workers independently};
> \end{tikzpicture}
> \end{document}
> ```

---

## 11. Known Technical Debt

### Critical Issues

| Issue | Location | Impact |
|-------|----------|--------|
| Placeholder JWT secret | `backend/.env` | Anyone can forge tokens in production |
| No structured logging | Throughout | `print()` and bare `logger.info()` with no consistent structure |
| `except: pass` in PDF extraction | `pdf_extractor.py:93` | Silently swallows image extraction errors |
| SurrealDB connection deadlock risk | `db.py` | `asyncio.Lock()` + `wait_for` can deadlock if `_do_connect` hangs inside the lock |
| No migration system | `db.py:_init_schema` | Schema recreated on every startup — safe for dev only |

### Code Quality Issues

| Issue | Location | Impact |
|-------|----------|--------|
| Global singletons (module-level) | `openrouter.py`, `provider_router.py`, `rag.py` | No DI — hard to mock/test |
| Fake token counting | `chunker.py` | Uses `len(text.split())` for overlap position (not token-accurate) |
| Direct SurrealQL in every module | All DB-calling files | No query builder — SQL injection risk from unsanitized input |
| `print()` statements | Multiple files | Should use logging |
| `except: pass` | `db.py:277-278`, `pdf_extractor.py:93` | Silently hides real errors |
| No rate limiting on LLM calls | Throughout | Can burn through API quotas |
| Slow ingestion (no parallelism) | `rag.py`, `pdf_extractor.py` | PDF extraction runs in a single thread |
| Bloom-level classification skipped | `routers/query.py:77` (`ponytail:` comment) | Feedback endpoint does not classify Bloom level — `ks.update_state` uses default `bloom_level=0` |

### Architectural Issues

| Issue | Impact |
|-------|--------|
| No database abstraction layer | Every module writes raw SurrealQL — impossible to swap DB |
| No IoC container | Services created as module-level singletons |
| Long-lived `httpx.AsyncClient` singleton | Socket pool shared across all requests |
| SSE streaming without backpressure | Can OOM if client is slow |
| File-based image storage (no CDN) | Images stored on backend filesystem under `./chat_images/` |

---

## 12. Status & Deferred Items

### Current Status (as of 2026-07-28)

| Area | Status |
|------|--------|
| Auth (login, register, JWT, RBAC) | ✅ Complete |
| PDF ingestion (text + images) | ✅ Complete |
| Hybrid search (BM25 + vector + RRF) | ✅ Complete |
| Streaming Q&A with citations | ✅ Complete |
| Course CRUD | ✅ Complete |
| Quiz generation + save | ✅ Complete |
| Flashcard generation + save | ✅ Complete |
| Exam paper generation | ✅ Complete |
| Analytics (query logs, coverage, gaps) | ✅ Complete |
| Learning path (ZPD recommendations) | ✅ Complete |
| Admin dashboard (users, stats) | ✅ Complete |
| Frontend pages (student, faculty, admin) | ✅ Complete |
| Docker deployment (5 services) | ✅ Complete |
| LLM multi-key rotation | ✅ Complete |
| E2E tests (Playwright) | ✅ Partial |
| Async query pipeline (Celery + Redis streaming) | ✅ Complete |
| Chat session recovery (sessionStorage) | ✅ Complete |

### Deferred / Missing

**Backend:**
- Student-level stats endpoint
- Activity/heatmap endpoint
- Faculty activity log
- Engagement metrics
- Course mastery endpoint

**Frontend:**
- Quiz page uses mock data
- Flashcards page uses mock data
- Curriculum file listing in faculty upload page

**Enhancement Backlog:**
- Speech-to-text input
- PDF export for generated papers
- "Regenerate questions" for quizzes
- Chat session isolation (per-course scoping)
- httpOnly cookie-based tokens (vs localStorage)

**Known issues:**
- `require_role` not applied to all non-admin routes (some rely on middleware only)
- `Depends(get_current_user)` not used on all routes
- Quiz/flashcards frontend pages show placeholder data
- Analytics batch endpoint not implemented
- Faculty analytics page uses mock data
- Faculty activity log not built

---

*End of Implementation Reference. This document covers the full codebase as of 2026-07-28.*
