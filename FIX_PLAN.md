# Fix Plan for Adaptive Learning Platform

## Issues Summary Table

| # | Priority | Issue | Root Cause | Fix |
|---|----------|-------|------------|-----|
| 1 | P0 | Page numbers always 1 | PDF extraction doesn't insert `[Page N]` markers; regex finds nothing → returns default 1 | Insert `[Page N]` markers in `extract_all_pages()` output |
| 2 | P0 | Index mismatch in `ingest()` | `embeddings` indexes by filtered `chunk_texts`, loop iterates unfiltered `raw_chunks` | Sync indices or use parallel iteration |
| 3 | P0 | Stale chunks on re-upload | Dedup uses `content_hash` (exact binary match); different file → new record, old chunks never deleted | DELETE existing chunks with same `source_title` + `course_code` before inserting new ones |
| 4 | P1 | Topic analysis not visible after upload | No GET endpoint fetches `document.topic_analysis` from DB; only task polling returns it (expires in 1h) | Add `GET /courses/{code}/documents` endpoint or include `topic_analysis` in stats response |
| 5 | P1 | Document list only shows names | `get_course_stats()` returns `documents: [{name}]` — no metadata | Include `topic_analysis`, `file_size`, `created_at` in document entries |
| 6 | P1 | `doc_count` always 0 | `get_batch_stats()` hardcodes `documents: []` | Query `document` table or `text_chunk.source_title GROUP BY` for counts |
| 7 | P1 | Failed tasks stuck in "Processing" | Polling FAILURE branch clears interval but doesn't update file status to 'error' | Set status to 'error' on task FAILURE |
| 8 | P1 | Stats not refreshed after completion | `invalidateQueries()` called at start only, not on SUCCESS | Invalidate stats again when polling detects SUCCESS |
| 9 | P2 | Classification fails without curriculum | `classify_sections_llm()` returns None if `course_topic` empty; embedding fallback also None if no topic embeddings | Add fallback to keyword-based topic assignment when both methods fail |
| 10 | P2 | No transaction isolation | Sequential inserts (chunks→images→document) with no rollback | Add cleanup pass: if document insert fails, DELETE already-inserted chunks using batch marker |
| 11 | P2 | Embedding failure drops entire topic group | Exception in `embed_text_batch` → ALL chunks in topic group get `emb=None` → skipped | Attempt individual embedding as fallback, or log chunks lost |
| 12 | P2 | Metadata not forwarded to text chunks | `**metadata` spread on image chunks but not text chunks | Add `**(metadata or {})` to text chunk dict |
| 13 | P2 | Physical files not deleted | `delete_material` removes DB records only | Query `file_path` from document record and delete the file |
| 14 | P3 | `/tasks` not in PUBLIC_PREFIXES | Auth middleware blocks direct API calls | Add `/tasks` to `PUBLIC_PREFIXES` tuple |
| 15 | P3 | Overly broad autoretry | `autoretry_for=(ValueError,)` catches API errors, not just transient issues | Be specific about retryable exceptions |
| 16 | P3 | Arbitrary module detection | Based on `order_index` gap > 2 heuristic | Replace with explicit module field or remove gap heuristic |
| 17 | P3 | Topic analysis overwrites multi-file | `setTopicAnalysis` shared state; last file wins | Keep per-file analysis or append to list |

## Implementation Steps

### Step 1: Fix Page Numbers (P0#1)
- Modify `backend/app/pdf_extractor.py:extract_all_pages()` to insert `[Page N]` markers
- This will enable proper page tracking in chunks

### Step 2: Fix Legacy Ingestion Index Mismatch (P0#2)
- Modify `backend/app/rag.py:ingest()` method to use consistent indexing
- Either filter raw_chunks first or use parallel iteration

### Step 3: Prevent Stale Chunks on Re-upload (P0#3)
- Modify `backend/app/rag.py:ingest_pdf()` to delete existing chunks with same source_title before inserting new ones

### Step 4: Expose Topic Analysis Persistently (P1#4, P1#5)
- Add `GET /courses/{course_code}/documents` endpoint in `backend/app/routers/courses.py`
- Modify `get_course_stats()` in `backend/app/rag.py` to include topic_analysis and file_size in documents list

### Step 5: Fix Document Count in Course Listing (P1#6)
- Modify `get_batch_stats()` in `backend/app/rag.py` to query actual document counts

### Step 6: Fix Frontend Upload Lifecycle (P1#7, P1#8)
- Modify `new_frontend/src/app/faculty/course/[code]/page.tsx`:
  - Set file status to 'error' on task FAILURE
  - Invalidate stats queries on task SUCCESS

### Step 7: Add Classification Fallback (P2#9)
- Modify `backend/app/topics.py` to add heading-based topic matching when curriculum doesn't exist

### Step 8: Delete Physical Files on Document Delete (P2#13)
- Modify `backend/app/routers/ingestion.py:delete_material()` to delete the actual PDF

### Step 9: Forward Metadata to Text Chunks (P2#12)
- Add `**(metadata or {})` to text chunk insert dict in `backend/app/rag.py`

### Step 10: Add /tasks to PUBLIC_PREFIXES (P3#14)
- Modify `backend/server.py` to include `/tasks` in PUBLIC_PREFIXES

## Files to Modify
1. `backend/app/pdf_extractor.py`
2. `backend/app/rag.py` (multiple functions)
3. `backend/app/topics.py`
4. `backend/app/routers/courses.py`
5. `backend/app/routers/ingestion.py`
6. `backend/server.py`
7. `new_frontend/src/app/faculty/course/[code]/page.tsx`

## Verification
After implementing these changes:
- All tests should pass
- Multi-file uploads should work correctly
- Topic analysis should persist beyond initial upload
- Document list should show meaningful metadata
- Page numbers should be accurate in citations
- Failed uploads should show error state