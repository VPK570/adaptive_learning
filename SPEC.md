# Adaptive Learning Platform — MVP Specification
## AI-Powered Socratic Tutor for BAECE102 (Digital Logic Design)

**Date:** May 2026
**Stack:** Python · FastAPI · ChromaDB · Next.js 16 · Tailwind CSS v4 · OpenRouter (free models)
**Scope:** Full-stack RAG pipeline + web API + chat UI

---

## 1. What This MVP Is

A **full-stack multimodal RAG pipeline** that:
1. **Ingest PDFs** — extract text AND images from every page
2. **Embed images natively** — Nemotron VL embeds images without captioning
3. **Two ChromaDB collections** — separate text and image embeddings (dimension mismatch)
4. **Retrieve** — both text and image chunks, filtered by course
5. **Query** — LLM (via OpenRouter) answers with cited, grounded Socratic responses
6. **Serve** — FastAPI REST API + Next.js chat UI

No Docker. No paid APIs. ChromaDB runs in-process.

---

## 2. Files

```
adaptive_learning/
├── README.md               # Run instructions
├── SPEC.md                 # This file
├── rag_pipeline/
│   ├── server.py           # FastAPI REST API
│   ├── main.py             # CLI: ingest | ingest-batch | query | eval | stats
│   ├── requirements.txt    # All dependencies (chromadb, fastapi, etc.)
│   ├── .env                # User's OPENROUTER_API_KEY
│   ├── .env.example        # Template
│   └── app/
│       ├── config.py       # Model IDs, chunk sizes, limits
│       ├── db.py           # ChromaDB (text_chunks + image_chunks collections)
│       ├── chunker.py      # 512-token sentence-aware
│       ├── citation.py     # Citation enforcement [Source: title, Slide N]
│       ├── openrouter.py   # Lazy singleton, batch embed, error handling
│       ├── pdf_extractor.py  # Magic byte validation, image extraction
│       ├── rag.py          # Two-collection RAG: ingest + retrieve
│       ├── query_engine.py   # Socratic prompting, context window
│       └── evaluator.py    # RAGAS-style evaluation (via Ring)
├── frontend/
│   ├── app/
│   │   ├── layout.tsx      # Root layout
│   │   ├── page.tsx        # Full chat UI (user/assistant bubbles, sidebar)
│   │   └── globals.css     # Tailwind v4
│   ├── package.json        # next@16, react@19, tailwind v4
│   ├── next.config.ts
│   └── tsconfig.json
└── tests/
    └── rag_pipeline/
        ├── conftest.py     # ChromaDB fixtures
        └── test_rag.py     # All tests
```

---

## 3. Models (OpenRouter — free)

| Use | Model | Notes |
|-----|-------|-------|
| Embeddings | `nvidia/llama-nemotron-embed-vl-1b-v2:free` | Multimodal — embeds text AND images natively |
| Reasoning/LLM | `inclusionai/ring-2.6-1t:free` | Thinking model; `thinking: {type: "disabled"}` returns final answer directly |

**Dimension mismatch:** Nemotron outputs different vector dimensions for text vs images. Two separate ChromaDB collections solve this:
- `text_chunks` — text content (384-dim via text-only endpoint)
- `image_chunks` — images embedded via multimodal endpoint (1024-dim)

---

## 4. Multimodal RAG Flow

### 4.1 Ingestion

```
PDF
  ├── Text extraction (pypdf) → per page → raw text
  └── Image extraction (pypdf /XObject) → raw bytes → magic byte validation

Text → chunk (512 tokens, sentence-aware) → embed_text_batch() → text_chunks collection
Images → embed_images() (Nemotron VL, native multimodal) → image_chunks collection
```

**No captioning needed** — Nemotron VL embeds images directly.

### 4.2 Retrieval

```
Query → embed_text() via OpenRouter
  → ChromaDB (query both collections in parallel)
  → Merge results → sort by distance
  → Returns top-k chunks (5 text + 5 image by default)
```

### 4.3 Query

```
Query + Chunks
  ├── Text chunks → <Text N: title, Slide N> ... </Text N>
  └── Image chunks → <Image N: title, Slide N> ... </Image N>

Context window → Socratic system prompt → Ring LLM → Citation validation → Response
```

---

## 5. API Routes

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/stats?course_code=BAECE102` | Course stats |
| `POST` | `/ingest` | Upload & ingest PDF (multipart form) |
| `POST` | `/query` | Full RAG query → Socratic response |
| `GET` | `/chunks?query=...&top_k=5` | Debug: raw retrieved chunks |

---

## 6. CLI Commands

```bash
# Ingest all PDFs
python main.py ingest-batch \
  --course BAECE102 \
  --dir /home/krishna/Downloads/dld \
  --glob "*.pdf"

# Query
python main.py query \
  --course BAECE102 \
  --question "Explain the state diagram for a modulo-6 counter" \
  --top-k 5

# Evaluate
python main.py eval --course BAECE102 --cases 10 --report

# Stats
python main.py stats --course BAECE102
```

---

## 7. Key Design Decisions

### Magic Byte Validation
Many PDF images are CCITT fax, JPEG2000, or LZW-compressed. Only standard JPEG (`FF D8 FF`), PNG (`89 50 4E 47`), WebP (`57 45 42 50`), GIF (`47 49 46 38`), and TIFF (`49 49 2A` / `4D 4D 00 2A`) are sent to the API. Others are skipped.

### Batch Image Embedding
OpenRouter has a 26 MB payload limit. Images batched in groups of 5. Large PDFs capped at 50 images (config: `IMAGE_MAX_PER_PDF=50`).

### Lazy Singleton for OpenRouter Client
Module-level `client = OpenRouterClient()` runs at import time BEFORE `load_dotenv()`. Solution: `_client_singleton = None`, initialized on first use via `get_client()`.

### Two-Collection ChromaDB
- `text_chunks`: text-only content, embedded via `embed_text_batch()`
- `image_chunks`: images embedded via `embed_images()` (multimodal)
- `retrieve()` queries both in parallel and merges results

---

## 8. Environment Variables

```env
OPENROUTER_API_KEY=sk-or-v1-...         # Required — from openrouter.ai/keys
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
EMBEDDING_MODEL=nvidia/llama-nemotron-embed-vl-1b-v2:free
LLM_MODEL=inclusionai/ring-2.6-1t:free
CHROMA_PATH=./chroma_db
RAG_TOP_K=5
CHUNK_SIZE=512
CHUNK_OVERLAP_TOKENS=64
IMAGE_MAX_PER_PDF=50
IMAGE_BATCH_SIZE=5
```

---

## 9. Success Criteria

| Metric | Target |
|--------|--------|
| All 6 PDFs ingested | 54 text + 93 image = 147 chunks |
| Server health endpoint | 200 OK |
| Query returns Socratic response | With citations |
| Frontend builds | `npm run build` passes |
| Tests pass | 100% |

---

## 10. What's Done ✅

- RAG pipeline (two collections, magic byte validation, batch embedding)
- FastAPI server (health, ingest, query, stats, chunks)
- Next.js 16 frontend (chat UI, markdown rendering, sidebar)
- Config, openrouter client, chunker, citation enforcement
- RAGAS-style evaluator
- Comprehensive README.md