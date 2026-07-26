# UniAI: Development Roadmap & Novel Feature Plan

## 1. Context: Where We Started

UniAI is a course-bound AI tutoring platform built at VIT Vellore. As of July 2026,
it has a working 7-stage RAG pipeline that enforces source-grounded answers,
citation validation, and mastery-adaptive Socratic pedagogy mapped to Bloom's
Taxonomy levels. Four patent claims were drafted covering the existing
architecture (two-collection multimodal RAG, automated uncited claim removal,
multi-stage Socratic pipeline, and Bloom's-constrained exam generation).

The professor (Dr. +91 94461 71877) identified two gaps in the current system:

1. **Bloom's Taxonomy classification** is a single black-box LLM call — no
   inspectable signals, no confidence scoring, no verification that the
   generated response matches the intended cognitive level.
2. **Academic integrity enforcement** is purely prompt-level — three lines in
   the system prompt ("Never write complete assignment solutions") with zero
   programmatic enforcement. No answer leakage prevention exists.

These gaps led to a deep research phase exploring novel directions that could
yield patents and publications.

---

## 2. Research Process

### 2.1 Codebase Audit
The existing codebase (`backend/app/`) was thoroughly examined:

| File | Existing State | Gap |
|------|---------------|-----|
| `bloom_classifier.py` | Single LLM call, prompt → int. No signals, features, or confidence. | No multi-signal fusion, no margin handling, no closed-loop verification |
| `query_engine.py:100-102` | Three prompt-level safety rules | No programmatic integrity enforcement |
| `validation.py:64-96` | 9 injection-detection regex patterns | Security-focused, not integrity-focused |
| `gatekeeper.py` | Course relevance check only | No integrity or leakage awareness |
| `verifier.py` | Answer grounding check | Grounding, not leakage detection |
| `knowledge_state.py` | Simple 0.15 learning rate mastery update | No personalized forgetting modeling |
| `query_enhancer.py` | Generates 3 diverse search queries | No sub-question decomposition |
| `deep_kt.py` | Stubbed, `DKT_ACTIVE=False` | Incomplete, no forgetting curve integration |

A `# ponytail:` comment at `query.py:77` explicitly marks the heuristic
Bloom classifier as missing — confirming the gap was known.

### 2.2 Literature Review (24 candidate ideas across 4 categories)

**Category 1: Knowledge Tracing & Student Modeling**
| Idea | Verdict | Reason |
|------|---------|--------|
| Multi-modal KT | ❌ Skip | MMKT (IEEE TCSS 2025), LEA (2026) already solve this |
| Uncertainty-aware KT | ❌ Skip | UKT (AAAI 2025) with code released — solved |
| Cross-course transfer | ❌ Skip | TransKT (IJCAI 2025), ACKT (WWW 2026) — solved |
| KG from PDFs | ❌ Skip | InstructKG, CourseMapper (2025) — commoditized |
| Interaction-based KT | ❌ Skip | LLMKT (LAK 2025), DiaCDM — solved |
| **Personalized forgetting curves** | ✅ **Adopt** | Gap: FSRS uses 19 global params, DKT has no explicit forgetting. No one learns per-student decay/strength/threshold parameters in a neural KT framework. |

**Category 2: Assessment & Content Generation**
| Idea | Verdict | Reason |
|------|---------|--------|
| KG-based question generation | ❌ Skip | KNIGHT, KAQG, Q-Chain — solved |
| Adaptive explanation generation | ❌ Skip | CLAF (EMNLP 2025), SNAPE-PM — solved |
| Metacognitive wrappers | ❌ Skip | MetaCLASS (2026), well-established |
| Pedagogical constraint satisfaction | ❌ Skip | MC-CPO, MWO — solved |
| **Adversarial question generation** | ❌ Defer | GapProbe (AAAI 2026) just done it. Medium novelty, high effort. |
| **Citation-backed short-answer grading** | ❌ Defer | Medium novelty but tangential to core tutor. |

**Category 3: Multi-Agent & Dialogue**
| Idea | Verdict | Reason |
|------|---------|--------|
| Multi-agent dialogue | ❌ Skip | KELE (EMNLP 2025), IntelliCode — solved |
| Dialogue act scaffolding | ❌ Skip | BIPED (2024), EDF (AAAI 2026) — solved |
| Contrastive student representation | ❌ Skip | MSCL (2026), CORE, Coral — solved |
| Misconception detection | ❌ Skip | MiRAGE (MAP@3 0.93) — saturated |
| RL strategy selection | ❌ Defer | Medium novelty but high effort (needs reward modeling + student simulation) |
| **Pedagogical CoT auditing** | ✅ **Adopt** | Gap: TRACE audits *whether* answers drove reasoning. No one makes pedagogical rationale a structured inspectable *output*. |

**Category 4: Evaluation, Fairness & Ethics**
| Idea | Verdict | Reason |
|------|---------|--------|
| Pedagogical quality scoring | ❌ Skip | MRBench (2025), BEA 2025 shared task — solved |
| Curriculum alignment verification | ❌ Skip | QuizWeaver, Curriculum Cartographer — solved |
| Bias detection in content | ❌ Defer | Medium novelty, but tangential to core pipeline |
| **Equity monitoring dashboard** | ✅ **Adopt** | Gap: All equity dashboards track *outcomes* (grades). None track *tutoring process quality* per demographic slice (leakage rate, scaffolding depth, citation quality). |
| **Red teaming benchmark** | ❌ Defer | Hot area (SafeTutors, EduGuardBench, SHAPE all 2026). Useful but not core. |
| **Answer-driven reasoning detection** | ❌ Defer | Single paper (Shen+ 2026), limited to math. Novel but specialized. |

### 2.3 Selection Rationale

From 24 candidates, **5 features** were selected plus **2 bonuses**:

**Selected — Core Differentiation:**
1. **Multi-Signal Bloom's Detector** — Paper only. The ε-tolerance margin and closed-loop verification are genuinely novel hooks in a saturated field.
2. **Leakage Scoring + Differential Redaction** — Patent + paper. Continuous scoring + type-aware decomposition + DP-style redaction has zero prior art. Hot emerging field.
3. **Pedagogical CoT Auditing** — Patent + paper. Making pedagogical rationale a structured inspectable artifact. Only TRACE (July 2026) comes close.
4. **Equity Monitoring Dashboard** — Patent + paper. First system to track tutoring *process* quality per demographic slice.
5. **Personalized Forgetting Curves** — Journal paper only. Bridges FSRS and DKT with per-student parameter estimation.

**Bonus — Enhancement:**
6. **Query Decomposition** — Paper only. Sub-question generation for multi-hop RAG retrieval. Modest novelty, low implementation cost.
7. **Red Teaming Benchmark** — Benchmark paper. Standardized adversarial safety evaluation. Timely but not core.

---

## 3. Architecture Plan

### 3.1 Current Pipeline (7 Stages)

```
Gatekeeper → Hybrid Retrieval → Context Assembly → Strategy Generation → LLM Response → Verifier → Citation Validation
```

### 3.2 Proposed Pipeline (10 Stages)

```
Bloom Detection → Gatekeeper → Retrieval → [Query Decomposition] → Context Assembly → Strategy Generation → LLM Response → Verifier → Integrity Enforcement → Citation Validation
    (stage 0)      (stage 1)   (stage 2)     (stage 3 — bonus)       (stage 4)          (stage 5)        (stage 6)    (stage 7)       (stage 8)           (stage 9)
```

- `[ ]` = gated by feature flag
- Stages 4-9 unchanged from current (Context, Strategy, LLM, Verifier, Citation)
- New stages: Bloom Detection (pre-gatekeeper), Query Decomposition (post-retrieval), Integrity Enforcement (post-verifier)

### 3.3 New Modules (11 files)

```
backend/app/
├── bloom_signals.py            # 6 signal extractors (verb, syntax, interrogative, scope, presupposition, answer-type)
├── bloom_fusion.py             # Calibrated weight fusion + ε-tolerance margin
├── bloom_verifier.py           # Closed-loop: re-apply signals to generated response
├── answer_decomposer.py        # Classify expected answer type: numeric/code/proof/short-answer/essay
├── leakage_scorer.py           # Continuous multi-dimensional leakage scoring
├── differential_redactor.py    # Type-aware DP-style answer redaction
├── integrity_enforcer.py       # Orchestrator: decompose → score → redact
├── pedagogical_tracer.py       # Structured pedagogical rationale trace generation
├── equity_monitor.py           # Demographic-stratified quality aggregation
├── query_decomposer.py         # Sub-question generation for multi-hop retrieval (bonus)
└── red_teaming.py              # Adversarial test harness (bonus)
```

### 3.4 Modified Modules (9 files)

```
backend/app/
├── bloom_classifier.py         # Refactor: orchestrate signals → fusion → verifier. Keep LLM as fallback.
├── query_engine.py             # Insert new stages into pipeline. 3 lines for decomposition.
├── gatekeeper.py               # Extended for integrity pre-check (optional)
├── verifier.py                 # Extended for leakage verification fallback (optional)
├── knowledge_state.py          # Replace update_state() rule with per-student forgetting params
├── deep_kt.py                  # Reactivate + add per-student embedding + hypernetwork
├── db.py                       # New tables: integrity_log, equity_snapshot
├── config.py                   # Feature flags + thresholds for all new modules
└── analytics.py                # Equity metrics aggregation queries
```

---

## 4. Design Decisions (Locked)

| Decision | Answer | Rationale |
|----------|--------|-----------|
| Bloom: replace existing or parallel? | **Parallel fallback.** Signals first. LLM only when confidence < threshold. | Preserves working system, adds novel path. Confirms existing `# ponytail:` intent at query.py:77. |
| Leakage scoring: gate or annotate? | **Annotate + similarity gating.** Embedding sim > 0.8: pass. 0.5-0.8: LLM verifier. < 0.5: block. | Similarity = groundedness signal. Low similarity = off-curriculum = leaky. Deterministic pre-filter saves LLM cost. |
| Similarity check vs existing verifier? | **Complement.** Embedding-based pre-filter replaces LLM for high-confidence cases. LLM verifier only for the ambiguous band. | Tiered: fast path for easy cases, deep path for hard cases. |
| Equity dashboard dimensions | **Deferred.** To be decided during implementation. | Need to see what data is available and meaningful. |
| Forgetting curves: separate or deep integration? | **Separate module feeding into existing `update_state()`.** | Minimal blast radius. Existing get_state() unchanged. |
| Query decomposition: before or after enhancement? | **After enhancement, before retrieval.** Sub-questions added to same `search_queries` list. Existing dedup loop handles merging. | 3 lines of code in query_engine.py. Zero changes to RAG, context, or generation. |

---

## 5. Feature Details

### 5.1 Multi-Signal Bloom's Detector

**File:** `bloom_signals.py`, `bloom_fusion.py`, `bloom_verifier.py`

**What it does:** Replaces the single LLM call at `bloom_classifier.py:37-54` with 6 inspectable signals:

| Signal | Method | Implementation |
|--------|--------|---------------|
| Verb taxonomy match | POS-tag first verb, match against Bloom verb lists | NLTK `pos_tag` (already a dependency) |
| Syntactic complexity | Parse tree depth of question | NLTK `RegexpParser` |
| Interrogative type | Classify what/why/how/which/when/where | Regex patterns |
| Referential scope | Count of entities/concepts referenced | NER + entity count |
| Presupposition structure | Detect embedded clauses, presupposition triggers | Regex + dependency patterns |
| Predicted answer-type | What kind of answer is expected (definition, procedure, comparison, etc.) | LLM call (lightweight schema) |

**Fusion:** Calibrated weight vector w ∈ ℝ⁶, weighted sum → softmax → confidence score.
**ε-tolerance:** When top-2 scores differ by < ε, return multi-level label (e.g., "Understand/Apply").
**Closed-loop:** Re-run same signal extractors on generated response. If response Bloom level ≠ planned level, trigger corrective regeneration.

**Novelty:** Medium. ε-tolerance and closed-loop verification have no prior art in Bloom's classification literature (100+ papers).

### 5.2 Leakage Scoring + Differential Redaction

**Files:** `answer_decomposer.py`, `leakage_scorer.py`, `differential_redactor.py`, `integrity_enforcer.py`

**What it does:** Three-stage integrity enforcement pipeline:

**Stage 1 — Type-Aware Answer Decomposition (`answer_decomposer.py`)**
Classify the expected answer type for a student query:
- `numeric` — a single number or formula
- `code` — programming code
- `proof` — mathematical proof
- `short_answer` — 1-3 sentence explanation
- `essay` — multi-paragraph explanation

Per-type decomposition extracts the answer core (e.g., the specific number for numeric, the code block for code).

**Stage 2 — Continuous Leakage Scoring (`leakage_scorer.py`)**
Multi-dimensional score ∈ [0, 1] with sub-dimensions:
- **Directness**: Does the response directly contain the answer core?
- **Procedural reveal**: Does it give away key steps?
- **Completeness**: Does it provide the full solution vs. partial guidance?
- **Specificity**: Does it name specific values, variable names, line numbers?

Scoring via embedding similarity between response and answer core, plus structural heuristics per answer type.

**Stage 3 — Differential Redaction (`differential_redactor.py`)**
When leakage score > threshold:
- `numeric`: Replace specific numbers with placeholders ("___")
- `code`: Collapse code blocks, replace with pseudocode structure
- `proof`: Remove the final step, ask student to complete
- `short_answer`/`essay`: Remove key claim, keep scaffolding structure

**Integration with existing verifier:**
- Embedding sim > 0.8: response is well-grounded → pass (no LLM needed)
- Sim 0.5-0.8: ambiguous → existing LLM verifier makes the call
- Sim < 0.5: response is off-curriculum → block immediately

**Novelty:** High. Continuous scoring (not binary) + type-aware decomposition + differential redaction (not just blocking) has no prior art. Closest: Zhao et al. (ACL 2026) use binary leakage metric. PEARL uses multi-dimension but across pedagogical traits, not leakage. No existing work applies DP-style redaction to educational answer content.

### 5.3 Pedagogical CoT Auditing

**File:** `pedagogical_tracer.py`

**What it does:** Every tutor response includes a structured rationale trace before the actual content:

```
[PEDAGOGICAL_TRACE]
  student_state: partial_understanding("K-map minimization", confidence=0.55)
  detected_gap: cannot_transition("truth_table" -> "K-map_grouping")
  strategy_selected: scaffold_question(compare_adjacent_cells)
  avoided: ["direct_answer(leakage_risk=0.82)", "worked_example(student_mastery=0.62)"]
```

Generated via structured LLM call with schema validation (reusing `provider_router.py:chat_with_schema()`). The trace is:
- **Faithful**: Generated from the actual decision logic, not post-hoc
- **Structured**: Machine-parseable JSON schema
- **Inspectable**: Visible in UI for faculty, logged for auditing
- **Verifiable**: Claims in the trace can be checked against actual student state

**Novelty:** Medium-High. TRACE (Shen+ 2026) audits *whether* answers drove reasoning. This makes reasoning *visible upfront*. ES-LLMs logs decisions but not structured rationale. No prior art for pedagogical rationale as a structured output artifact.

### 5.4 Equity Monitoring Dashboard

**File:** `equity_monitor.py`

**What it does:** Background aggregation that tracks tutoring quality metrics per demographic slice:

| Metric | Definition | Source |
|--------|-----------|--------|
| Avg leakage score | Mean leakage_score per group | `integrity_enforcer.py` |
| Response length | Mean tokens per response | `query_engine.py` |
| Citation rate | % of responses with >=1 valid citation | `citation.py` |
| Scaffolding depth | Mean turns before hint escalation | `query_engine.py` |
| Gatekeeper refusal rate | % of queries refused | `gatekeeper.py` |
| Bloom distribution | % of responses at each Bloom level | `bloom_fusion.py` |

Dimensions (TBD during implementation): language, mastery band, course.

**Novelty:** High. All existing equity dashboards track *outcomes* (grades, pass rates). None track AI tutor *response quality per group*. FairTutor tracks access-tier equity, not demographic process equity.

### 5.5 Personalized Forgetting Curves

**Files:** `knowledge_state.py` (modify), `deep_kt.py` (reactivate)

**What it does:** Replaces the fixed 0.15 learning rate in `knowledge_state.py:update_state()` with per-student forgetting curve parameters:

- **γᵢ** (decay rate): How fast student i forgets
- **αᵢ** (initial strength): How well student i encodes new information
- **βᵢ** (retrieval threshold): How confident student i needs to be to answer correctly

These are learned as student-specific embeddings via a hypernetwork on top of the existing DKT model in `deep_kt.py`. Parameters update after each quiz interaction.

**Novelty:** Medium. CPF personalizes forgetting rates via embeddings. memoryKT computes a personalized score. No one learns a complete interpretable parameter set per student in a neural KT framework. Bridges the FSRS (global optimization) and DKT (deep learning) paradigms.

### 5.6 Query Decomposition (Bonus)

**File:** `query_decomposer.py`

**What it does:** Generates 2-5 sub-questions from a complex student query, added to the existing `search_queries` list for multi-query retrieval.

**Integration — 3 lines in `query_engine.py`:**
```python
# After query enhancement block (lines 254-261)
if settings.QUERY_DECOMPOSITION_ENABLED:
    from app.query_decomposer import decompose_query
    sub_questions = await decompose_query(query, course_ctx)
    search_queries.extend(sub_questions)
```

The existing dedup loop (lines 264-277) handles merging results from all queries.

**Graceful degradation:** On LLM failure, returns `[query]` — same as existing enhancer.

**Novelty:** Low. Query decomposition for RAG is standard practice (20+ papers). Paper angle is an ablation study in the lecture-scoped setting.

### 5.7 Red Teaming Benchmark (Bonus)

**File:** `red_teaming.py`

**What it does:** Adversarial test harness that evaluates the tutor against known attack types:
- Direct answer requests
- Emotional manipulation
- Intentional wrong answers (eliciting correction)
- Role-play / context manipulation
- Request shaping

Runs as a CLI tool, generates a report of attack success rates per defense layer.

**Novelty:** Medium. Multiple benchmarks in 2026 (SafeTutors, EduGuardBench, SHAPE). A *unified* benchmark could be novel but requires large annotation effort. Deferred.

---

## 6. Implementation Order & Phasing

### Phase 1: Patent Foundation (Priority: High)

**Goal:** Build enough to file 3 provisional patents. No public code push before filing.

| Step | Files | Effort | Depends On |
|------|-------|--------|------------|
| 1.1 | `answer_decomposer.py` | 1-2 days | — |
| 1.2 | `leakage_scorer.py` | 2-3 days | 1.1 |
| 1.3 | `differential_redactor.py` | 2-3 days | 1.1 |
| 1.4 | `integrity_enforcer.py` | 1 day | 1.2, 1.3 |
| 1.5 | `db.py` (integrity_log table) | 0.5 day | — |
| 1.6 | `config.py` (integrity flags) | 0.5 day | — |
| 1.7 | `query_engine.py` (insert integrity stage) | 0.5 day | 1.4 |
| — | **File Provisional #1** (leakage scoring) | — | After 1.4 |
| — | **File Provisional #2** (CoT auditing) | — | After 3.3 |
| — | **File Provisional #3** (equity monitoring) | — | After 4.2 |

### Phase 2: Bloom's Detector (Priority: High)

**Goal:** First paper submission.

| Step | Files | Effort | Depends On |
|------|-------|--------|------------|
| 2.1 | `bloom_signals.py` | 3-4 days | — |
| 2.2 | `bloom_fusion.py` | 2-3 days | 2.1 |
| 2.3 | `bloom_verifier.py` | 2 days | 2.1 |
| 2.4 | `bloom_classifier.py` (refactor) | 1 day | 2.1, 2.2, 2.3 |
| 2.5 | `config.py` (bloom flags) | 0.5 day | — |
| 2.6 | `query_engine.py` (insert bloom stage) | 0.5 day | 2.4 |

### Phase 3: Pedagogical Tracing (Priority: Medium)

**Goal:** Second patent + paper.

| Step | Files | Effort | Depends On |
|------|-------|--------|------------|
| 3.1 | `pedagogical_tracer.py` (schema + generation) | 2-3 days | — |
| 3.2 | `config.py` (trace flags) | 0.5 day | — |
| 3.3 | `query_engine.py` (insert trace generation) | 0.5 day | 3.1 |

### Phase 4: Equity Dashboard (Priority: Medium)

**Goal:** Third patent + paper.

| Step | Files | Effort | Depends On |
|------|-------|--------|------------|
| 4.1 | `analytics.py` (equity aggregation queries) | 2-3 days | Phase 1, 2 |
| 4.2 | `db.py` (equity_snapshot table) | 0.5 day | — |
| 4.3 | `equity_monitor.py` | 2 days | 4.1 |
| 4.4 | Frontend dashboard | 3-4 days | 4.3 |

### Phase 5: Forgetting Curves (Priority: Low)

**Goal:** Journal paper.

| Step | Files | Effort | Depends On |
|------|-------|--------|------------|
| 5.1 | `deep_kt.py` (reactivate + add hypernetwork) | 3-5 days | — |
| 5.2 | `knowledge_state.py` (replace update rule) | 1-2 days | 5.1 |
| 5.3 | `config.py` (forgetting flags) | 0.5 day | — |

### Phase 6: Bonuses (Priority: Lowest)

| Step | Files | Effort | Depends On |
|------|-------|--------|------------|
| 6.1 | `query_decomposer.py` | 1-2 days | — |
| 6.2 | `query_engine.py` (+3 lines) | 0.5 day | 6.1 |
| 6.3 | `config.py` (decomp flags) | 0.5 day | — |
| 6.4 | `red_teaming.py` | 3-5 days | Phase 1 |

---

## 7. Patent & Publication Pipeline

### 7.1 Patent Filings

| # | Title | Type | Filing Window | Claims |
|---|-------|------|--------------|--------|
| P1 | "System and Method for Type-Aware Answer Decomposition and Differential Redaction for Leakage Prevention in AI Tutoring" | Indian Provisional | Before any public code push | Type-aware decomposition, continuous multi-dim scoring, differential redaction per answer category |
| P2 | "Method for Generating and Validating Structured Pedagogical Rationale Traces in AI Tutoring Systems" | Indian Provisional | Within 6 months of P1 | Structured CoT rationale generation, schema-enforced trace validation, trace-based corrective regeneration |
| P3 | "System for Demographic-Stratified Monitoring of AI Tutoring Process Quality" | Indian Provisional | Within 6 months of P1 | Process quality metrics (not outcomes), demographic stratification, automated equity alerting |

### 7.2 Publication Pipeline

| # | Title | Venue | Type | Timeline |
|---|-------|-------|------|----------|
| 1 | "Multi-Signal Bloom's Taxonomy Classification with Epsilon-Tolerance Margin" | LAK / AIED | Workshop (6 pages) | After Phase 2 |
| 2 | "Differential Redaction: Preventing Answer Leakage in AI Tutors through Type-Aware Decomposition and Continuous Scoring" | ACL / AIED | Conference (8 pages) | After P1 filing |
| 3 | "Pedagogical Chain-of-Thought Auditing: Making Tutor Reasoning Inspectable" | AIED / EDM | Conference (8 pages) | After P2 filing |
| 4 | "Process Equity in AI Tutoring: A Dashboard for Monitoring Differential Response Quality" | LAK | Short (4 pages) | After P3 filing |
| 5 | "Per-Student Forgetting Curve Estimation: Bridging Spaced Repetition and Deep Knowledge Tracing" | IEEE TLT / EDM | Journal (12+ pages) | After Phase 5 |
| B1 | "Query Decomposition for Lecture-Scoped Retrieval-Augmented Generation" | SIGIR / ECIR | Short (4 pages) | Any time |
| B2 | "EduGuardBench: A Unified Red Teaming Benchmark for AI Tutoring Safety" | AAAI / ACL | Benchmark (8 pages) | After Phase 6 |

---

## 8. Pipeline Integration Detail

### 8.1 Current Flow (query_engine.py)

```
query_stream()/query()
  ├── _get_course_context()
  ├── gatekeeper.check_and_enrich()        # Stage 1: Relevance check
  ├── generate_search_queries()            # (inside) Query enhancement
  ├── rag_pipeline.retrieve() loop         # Stage 2: Hybrid retrieval
  ├── build_tutor_prompt()                 # Stage 3-4: Context + Strategy
  ├── client.stream() / client.chat()      # Stage 5: LLM generation
  ├── verifier.verify_answer()            # Stage 6: Grounding check
  └── extract_cited_sources()             # Stage 7: Citation validation
```

### 8.2 Proposed Flow

```
query_stream()/query()
  ├── _get_course_context()
  ├── bloom_signals + bloom_fusion         # NEW Stage 0: Bloom detection
  │   └── (skip if user manually selected bloom_level)
  ├── gatekeeper.check_and_enrich()        # Stage 1: Relevance check
  ├── generate_search_queries()            # Query enhancement
  ├── decompose_query()                    # NEW Stage 2b: Query decomposition (bonus)
  ├── rag_pipeline.retrieve() loop         # Stage 2: Hybrid retrieval
  ├── integrity_enforcer.pre_check()       # NEW: Pre-retrieval integrity scan
  ├── build_tutor_prompt()                 # Stage 3-4: Context + Strategy
  │   └── pedagogical_tracer.generate()    # NEW: Add trace to strategy
  ├── client.stream() / client.chat()      # Stage 5: LLM generation
  ├── verifier.verify_answer()            # Stage 6: Grounding check
  ├── integrity_enforcer.post_check()     # NEW Stage 8: Leakage scoring + redaction
  ├── bloom_verifier.verify()             # NEW: Closed-loop Bloom check
  └── extract_cited_sources()             # Stage 9: Citation validation
```

### 8.3 Query Decomposition Integration Detail

The query_decomposer.py module follows the exact pattern of query_enhancer.py:

```python
# query_decomposer.py (~60 lines)
import logging
from app.provider_router import router as client

logger = logging.getLogger(__name__)

DECOMPOSER_SCHEMA = {
    "type": "object",
    "properties": {
        "sub_questions": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "maxItems": 5,
        }
    },
    "required": ["sub_questions"],
}

async def decompose_query(query: str, course_context: dict, num_questions: int = 3) -> list[str]:
    """
    Generate sub-questions from a complex student query.
    Returns [query] on any failure — never blocks.
    """
    # ... (same pattern as generate_search_queries in query_enhancer.py)
    # System prompt asks LLM to break the query into independent sub-questions
    # that would each retrieve different relevant chunks
```

Integration in query_engine.py (3 lines):

```python
# After line 261 (query enhancement):
if settings.QUERY_DECOMPOSITION_ENABLED:
    from app.query_decomposer import decompose_query
    sub_qs = await decompose_query(query, course_ctx,
        num_questions=settings.QUERY_DECOMPOSITION_NUM_QUESTIONS)
    search_queries.extend(sub_qs)
```

**Behavior matrix:**

| Decomposition | Enhancement | Resulting queries | Use case |
|:---:|:---:|---|----|
| OFF | OFF | `[query]` | Simple single-aspect questions |
| OFF | ON | `[3 search variants]` | Standard RAG (current behavior) |
| ON | OFF | `[query + 3 sub-questions]` | Multi-aspect questions needing different contexts |
| ON | ON | `[3 variants + 3 sub-questions]` | Complex questions needing both recall boost and multi-hop |

**Config flags (config.py):**
```python
QUERY_DECOMPOSITION_ENABLED: bool = False
QUERY_DECOMPOSITION_NUM_QUESTIONS: int = 3  # 1-5
```

---

## 9. File Tree (Complete)

```
backend/
├── app/
│   ├── bloom_classifier.py        * MODIFY — orchestrate signals + fusion + verify
│   ├── bloom_signals.py            NEW — 6 signal extractors
│   ├── bloom_fusion.py             NEW — calibrated weights + ε-tolerance
│   ├── bloom_verifier.py           NEW — closed-loop verification
│   ├── answer_decomposer.py        NEW — type-aware answer classification
│   ├── leakage_scorer.py          NEW — continuous multi-dim scoring
│   ├── differential_redactor.py    NEW — DP-style answer redaction
│   ├── integrity_enforcer.py       NEW — orchestrator
│   ├── pedagogical_tracer.py       NEW — structured rationale traces
│   ├── equity_monitor.py           NEW — demographic quality aggregation
│   ├── query_decomposer.py         NEW — sub-question generation
│   ├── red_teaming.py              NEW — adversarial test harness
│   ├── query_engine.py            * MODIFY — insert new stages
│   ├── gatekeeper.py              * MODIFY — optional integrity pre-check
│   ├── verifier.py                * MODIFY — leakage verification fallback
│   ├── knowledge_state.py         * MODIFY — forgetting curve params
│   ├── deep_kt.py                 * MODIFY — reactivate + hypernetwork
│   ├── db.py                      * MODIFY — new tables
│   ├── config.py                  * MODIFY — feature flags + thresholds
│   └── analytics.py               * MODIFY — equity metrics
├── tests/
│   ├── test_bloom_signals.py       NEW
│   ├── test_leakage_scorer.py      NEW
│   ├── test_integrity.py           NEW
│   └── test_query_decomposer.py    NEW
└── (rest unchanged)
```

### Files NOT Touched

```
backend/
├── server.py                       — No changes (auto-mounts routers)
├── auth.py                         — No auth changes needed
├── rag.py                          — Retrieval unchanged
├── chunker.py                      — Chunking unchanged
├── provider_router.py              — LLM routing unchanged
├── citation.py                     — Citation unchanged
├── routers/                        — No router changes (existing API surface)
├── schemas.py                      — No schema changes (adding metadata in response, not request)
new_frontend/                       — Backend-only until dashboard phase
frontend/                           — Production frontend unchanged
```

---

## 10. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM cost increases from additional calls (bloom signals, decomposition, trace generation) | Medium | All LLM calls are lightweight (structured schemas, low max_tokens). Each has a fast fallback path. Leakage check uses embedding not LLM for high-confidence cases. |
| False positives in leakage scoring block legitimate pedagogical responses | High | Configurable thresholds. Annotation-first default. LLM verifier fallback for ambiguous cases. |
| Equity dashboard has insufficient data per demographic slice | Medium | Start with 2 dimensions only. Aggregate weekly, not per-session. |
| ε-tolerance margin produces too many multi-level labels | Low | ε is configurable. Default based on calibration experiments during Phase 2. |
| Forgetting curve training data insufficient | Medium | Use existing question_log data. Cold-start with population average, individualize with Bayesian updating. |
| Patent prior art search misses existing patents | Medium | Professional prior art search recommended before filing. |

---

## 11. Summary

5 core features + 2 bonuses, organized into 3 patent filings and up to 7 publications.

The differentiation strategy is:
1. **Mechanical enforcement over instructional prompting** — Integrity, citations, and Bloom alignment are hard constraints, not LLM instructions.
2. **Inspectability over black boxes** — Open signals, structured rationale traces, and demographic quality monitoring make every decision auditable.
3. **Pedagogical safety as a first-class constraint** — The system is designed to prevent harm (answer leakage, inequity, hallucination) by construction, not by instruction.

**Phased delivery:**
- Phase 1 (Patent prep): ~1-2 weeks
- Phase 2 (Bloom's detector): ~1 week
- Phase 3 (Pedagogical tracing): ~1 week
- Phase 4 (Equity dashboard): ~1 week
- Phase 5 (Forgetting curves): ~1 week
- Phase 6 (Bonuses): ~1 week
- **Total:** ~6-8 weeks for complete implementation
