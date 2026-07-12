# Deep Research Prompt — Adaptive Learning Platform (Patent & Paper Novelty)

Use this prompt with Perplexity, ChatGPT (web search), or any AI research tool.

---

Copy and paste the block below:

```

## PROJECT CONTEXT

I am building an **Adaptive Learning Platform** — a citation-verified AI tutor grounded in course materials. This is a complete web application (not a prototype) with the following architecture:

### Core Differentiator: Three-Layer Integrity Pipeline
1. **Gatekeeper Layer** — Blocks off-topic queries before they reach the LLM (e.g., "write my essay", "what's the weather", "solve this unrelated math problem"). Only syllabus-relevant questions proceed.
2. **Hybrid Retrieval Layer** — Combines keyword search (BM25/exact match) + semantic search (vector embeddings) with result fusion. Catches both exact terminology and conceptual matches.
3. **Verifier Layer** — Post-generation cross-check: every factual claim in the answer is validated against retrieved source chunks. Unsupported claims are flagged/removed.

### Enforced Academic Honesty
- **Mandatory per-claim citations** — Every sentence carrying factual content must cite a specific source document AND page number
- **Automated citation validation** — System verifies the cited text actually exists in the source at that page
- **Course-scoped grounding** — LLM is explicitly forbidden from using parametric knowledge; if answer not in materials, it says so
- **No hallucination fallback** — Unlike RAG systems that "try their best," this system refuses to invent

### Dual-User Ecosystem (Student + Faculty)
**Faculty Tools:**
- Course creation & curriculum management (upload PDFs, organize by module/topic)
- Automatic exam paper generation from course materials (with difficulty distribution, topic coverage)
- Analytics dashboard: student query patterns, weak topics, engagement metrics
- Content management: edit/delete courses, re-process PDFs

**Student Tools:**
- Socratic chat tutor (streaming responses, with citations inline)
- Quiz generation (multiple choice, short answer) from course content
- Flashcard generation (spaced repetition ready)
- Progress tracking per topic/module

### Technical Stack
- **Backend**: Python + FastAPI (async), JWT + bcrypt auth, rate limiting, prompt injection defenses
- **Frontend**: Next.js 14 + React (App Router), TypeScript, Tailwind CSS
- **Database**: SurrealDB (multi-model: document + graph + vector) — stores PDFs, embeddings, chat history, courses, users
- **AI Models**: OpenRouter API (open models: Llama 3, Mixtral, etc.) — self-hostable, no vendor lock-in
- **PDF Processing**: pypdf (text + image extraction), custom chunking with overlap
- **Search**: Hybrid BM25 + vector (sentence-transformers), reciprocal rank fusion
- **Deployment**: Docker Compose (single-command local deployment)

### Current State (From the Project Report:
- **What works**: Full PDF pipeline, hybrid search, AI tutor chat (streaming + citations + gatekeeper + verifier), course management, quiz/flashcard/exam generation, analytics, Docker setup, auth code written
- **What's left**: Turn on auth (currently disabled), role-based access, move secrets to env, strengthen prompt injection, switch DB to persistent storage, fix text chunking counter, reuse AI connections, restrict CORS, add logging/indexes/timestamps, clean up ChromaDB references

### Why This Is Different From Existing Tools
| Capability | NotebookLM / General RAG | Khanmigo / Quizlet | **Our Platform** |
|------------|--------------------------|-------------------|------------------|
| Source of answers | Uploaded docs + parametric | Curated + parametric | **Only course materials** |
| Hallucination control | Single-layer retrieval | Single-layer | **3-layer: gatekeeper + retrieval + verifier** |
| Citations | Optional source list | General references | **Mandatory per-claim, page-level, auto-validated** |
| Search | Vector-only | Vector-only | **Hybrid keyword + semantic, fused** |
| Off-topic queries | Answered anyway | Partial guardrails | **Blocked at gatekeeper** |
| Teacher toolkit | None / limited | Limited | **Full: exams, analytics, course mgmt** |
| Deployment | Cloud-only, vendor-locked | Cloud-only | **Self-hostable, open models, Docker** |

---

I need to identify NOVELTY for a patent and/or research paper. Conduct a thorough investigation covering:

I need to identify NOVELTY for a patent and/or research paper. Conduct a thorough investigation covering:

## 1. Patent Landscape
Search for granted patents and published patent applications on:
- RAG-based educational tutoring systems
- Multi-layer/hallucination verification pipelines for AI tutors
- Course-scoped answer grounding and off-topic query blocking
- Automated citation enforcement with page-level verification
- Hybrid search (keyword + semantic) for educational RAG
- Patents held by Khan Academy (Khanmigo), Quizlet (Q-Chat), Coursera, Chegg, NotebookLM

## 2. Academic Literature
Find papers on:
- Hallucination rates in RAG-based educational tools (Stanford/MIT studies)
- RAG failure points (especially "Seven Failure Points" paper)
- Socratic tutoring with LLMs
- Integrity/verification layers for LLM outputs
- Open-source vs proprietary models in education
- Prompt injection risks in educational AI

## 3. Existing Products — Deep Analysis
- NotebookLM — limitations on course-structuring, citation enforcement
- Khanmigo — how it handles grounding, does it have a verifier step?
- Quizlet Q-Chat, CheggMate, Course Hero — their RAG architectures
- Any university-built systems (Harvard, MIT, Stanford course-specific tutors)
- Existing open-source RAG tutors (LangChain-based, etc.)

## 4. Gap Analysis
Where does every existing product fall short on:
- Multi-layer verification (not just retrieval)
- Per-claim page-level citations
- Blocking off-topic queries entirely
- Full teacher toolkit (exam generation, analytics) integrated with grounded AI
- Self-hostable/open-model approach vs vendor lock-in

## 5. Novelty Angles for Patent
- Is the three-layer pipeline (gatekeeper → hybrid retrieval → verifier) patentable?
- Is "mandatory per-claim citation with automated validation" novel?
- Is "course-scoped AI with complete faculty ecosystem" a unique combination?
- Can the hybrid fusion search for educational material be claimed?
- What prior art exists for each angle?

## 6. Novelty Angles for Research Paper
- Where could we publish? (LAK, AIED, EDM, AAAI, NeurIPS datasets & benchmarks track)
- What benchmark/evaluation could we contribute? (hallucination rate benchmark for educational RAG?)
- What ablation study would be meaningful? (compare single-layer vs multi-layer RAG on real course data)
- Could we release a dataset of course-Q&A pairs with verified citations?

## 7. Competitor IP
Who would challenge a patent? Who has pending patents in this space?

## Output Format
For each section, give specific findings with links/sources, then a summary of the MOST promising novelty angles that are:
- (a) genuinely novel (not covered by prior art)
- (b) non-obvious to someone skilled in the art
- (c) practically useful and implementable
```

---

## Supplementary: Direct Patent Searches

Also search **Google Patents** and **USPTO** directly with:

- `"retrieval augmented generation" education tutor`
- `"multi-layer verification" chatbot`
- `"course material" grounding AI citation`
- `RAG hallucination detection patent`
- `"off-topic query" blocking AI tutor`
