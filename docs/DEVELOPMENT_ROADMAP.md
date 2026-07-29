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
| Idea | Verdict | Reason | Ref |
|------|---------|--------|-----|
| Multi-modal KT | ❌ Skip | MMKT fuses text/image/cognitive/KG modalities (~3.5% AUC over DKT). LEA deploys tri-modal agent in classroom. | [38], [39] |
| Uncertainty-aware KT | ❌ Skip | UKT (AAAI 2025) separates epistemic from aleatory uncertainty with Gaussian embeddings. Code released. | [23] |
| Cross-course transfer | ❌ Skip | TransKT (IJCAI 2025) uses LLM-built concept graphs + GCN. ACKT (WWW 2026) handles cross-disciplinary cold-start. | [40], [41] |
| KG from PDFs | ❌ Skip | InstructKG and CourseMapper provide end-to-end PDF-to-KG pipelines. Precision 1.0 on benchmarks. | [42], [43] |
| Interaction-based KT | ❌ Skip | LLMKT (LAK 2025) fine-tunes Llama-3.1-8B on dialogue KT. DiaCDM adds AMR graphs for cognitive diagnosis. | [44], [45] |
| **Personalized forgetting curves** | ✅ **Adopt** | Gap: FSRS [27] uses 19 global params across all students. CPF [24] and memoryKT [26] compute personalized scores but not full per-student parameter sets. | — |

**Category 2: Assessment & Content Generation**
| Idea | Verdict | Reason | Ref |
|------|---------|--------|-----|
| KG-based question generation | ❌ Skip | KNIGHT uses topic KG for difficulty-controlled MCQ generation. KAQG and Q-Chain do KG-enhanced RAG QG. | [46], [47] |
| Adaptive explanation generation | ❌ Skip | CLAF (EMNLP 2025) adapts complexity and style via KG retrieval + preference learning. SNAPE-PM uses Bayesian partner modeling. | [48], [49] |
| Metacognitive wrappers | ❌ Skip | MetaCLASS formalizes 11 metacognitive coach moves with turn-level NO_INTERVENTION. Well-established in learning sciences. | [50] |
| Pedagogical constraint satisfaction | ❌ Skip | MC-CPO provides RL with mastery-conditioned action spaces. MWO solves multi-objective ACS via memetic optimization. | [51], [52] |
| **Adversarial question generation** | ❌ Defer | GapProbe (AAAI 2026) generates counterfactual follow-ups targeting KG-probed knowledge gaps. Medium novelty, high effort. | [53] |
| **Citation-backed short-answer grading** | ❌ Defer | Fateen et al. (2024) uses RAG for scoring + feedback with citations. Medium novelty, tangential to core tutor. | [54] |

**Category 3: Multi-Agent & Dialogue**
| Idea | Verdict | Reason | Ref |
|------|---------|--------|-----|
| Multi-agent dialogue | ❌ Skip | KELE (EMNLP 2025) uses consultant-teacher dual-agent. IntelliCode (EACL 2026) has 6 specialized agents. | [35], [36] |
| Dialogue act scaffolding | ❌ Skip | BIPED defines 34 tutor acts + 9 student acts with predict-act-generate. EDF (AAAI 2026) uses Evidence-Decision-Feedback. | [37], [65] |
| Contrastive student representation | ❌ Skip | MSCL (2026) self-supervised graph contrastive for KT. Coral does collaborative CD with disentangled representation. | [59], [60] |
| Misconception detection | ❌ Skip | MiRAGE achieves MAP@3 of 0.93 via retrieval-guided reasoning. ACL 2026 knowledge distillation reaches MAP@3 0.9585. | [61], [62] |
| RL strategy selection | ❌ Defer | PEARL trains Socratic tutors via multi-objective RL. MHPO (ACL 2026) does multi-horizon preference optimization. High effort. | [10], [63] |
| **Pedagogical CoT auditing** | ✅ **Adopt** | Gap: TRACE [14] audits *whether* answers drove reasoning. No one makes pedagogical rationale a structured inspectable *output*. | — |

**Category 4: Evaluation, Fairness & Ethics**
| Idea | Verdict | Reason | Ref |
|------|---------|--------|-----|
| Pedagogical quality scoring | ❌ Skip | MRBench [55] defines 8-dimension evaluation taxonomy. BEA 2025 shared task [56] operationalized 4 dimensions. | [55], [56] |
| Curriculum alignment verification | ❌ Skip | QuizWeaver [57] enforces deterministic Bloom's/Webb's DOK alignment. Curriculum Cartographer [58] achieves ICC=0.874 with expert judges. | [57], [58] |
| Bias detection in content | ❌ Defer | Gupta et al. (FAccT 2026) [18] found 2.55 grade-level gaps for marginalized profiles. Medium novelty, tangential. | [18] |
| **Equity monitoring dashboard** | ✅ **Adopt** | Gap: All equity dashboards [19] track *outcomes* (grades). None track *tutoring process quality* per demographic slice (leakage rate, scaffolding depth, citation quality). FairTutor [20] tracks access-tier equity only. | — |
| **Red teaming benchmark** | ❌ Defer | Hot area: SafeTutors [17] (11 harm dimensions), EduGuardBench [64], SHAPE [12] (9,087 question pairs). Useful but not core. | [17], [12], [64] |
| **Answer-driven reasoning detection** | ❌ Defer | Single paper [14] (Shen+ 2026), limited to math. Novel but specialized. Generalization beyond math numeric is open. | [14] |

### 2.3 Novelty Summary

| Category | Idea | Verdict | Patent | Paper | Key Reference |
|----------|------|---------|--------|-------|---------------|
| KT | Personalized forgetting curves | ✅ Adopt | ❌ | ✅ Journal | Bridging FSRS [27] and DKT gap |
| Assessment | Adversarial question generation | ❌ Defer | ❌ | ✅ Conf | GapProbe (AAAI 2026) |
| Assessment | Citation-backed grading | ❌ Defer | ❌ | ✅ Conf | Fateen et al. (2024) |
| Dialogue | Pedagogical CoT auditing | ✅ Adopt | ✅ | ✅ Conf | TRACE [14] comparison |
| Dialogue | RL strategy selection | ❌ Defer | ❌ | ✅ Conf | PEARL [10] |
| Eval/Ethics | Equity monitoring dashboard | ✅ Adopt | ✅ | ✅ Short | No prior art for process equity |
| Eval/Ethics | Red teaming benchmark | ❌ Defer | ❌ | ✅ Bench | SafeTutors [17] |
| Eval/Ethics | Bias detection | ❌ Defer | ❌ | ✅ Conf | Gupta et al. (FAccT 2026) |
| Eval/Ethics | Answer-driven reasoning | ❌ Defer | ❌ | ✅ Conf | TRACE [14] |
| Core | Multi-Signal Bloom's Detector | ✅ Adopt | ❌ | ✅ Workshop | ε-tolerance + closed-loop |
| Core | Leakage Scoring + Diff Redaction | ✅ Adopt | ✅ | ✅ Conf | Novel combination |
| Bonus | Query Decomposition | ✅ Bonus | ❌ | ✅ Short | Ammann et al. (ACL 2025) |
| Bonus | Red Teaming Benchmark | ✅ Bonus | ❌ | ✅ Bench | SafeTutors [17] |

### 2.4 Selection Rationale

From 24 candidates, **5 features** were selected plus **2 bonuses**:

**Selected — Core Differentiation:**
1. **Multi-Signal Bloom's Detector** — Paper only. The ε-tolerance margin and closed-loop verification differentiate from 100+ existing papers (SOTA: Alammary & Masoud 2025, 96% [1]).
2. **Leakage Scoring + Differential Redaction** — Patent + paper. No existing work combines continuous scoring with type-aware decomposition and DP-style redaction. Related: binary leakage [9], multi-dimension pedagogical scoring [10], safe RAG [11].
3. **Pedagogical CoT Auditing** — Patent + paper. Only TRACE [14] is adjacent (audits answer-driven reasoning, not rationale). ES-LLMs [17] logs decisions but not structured traces.
4. **Equity Monitoring Dashboard** — Patent + paper. First system to track tutoring *process* quality per demographic slice. Outcome equity dashboards exist [19]; process equity does not.
5. **Personalized Forgetting Curves** — Journal paper only. FSRS [27] uses 19 global params. CPF [24] and memoryKT [26] compute personalized scores but not full interpretable parameter sets.

**Bonus — Enhancement:**
6. **Query Decomposition** — Paper only. Sub-question generation for multi-hop RAG. Modest novelty (Ammann et al. ACL 2025 [29], Petcu et al. EACL 2026 [30]).
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

**Novelty:** Medium. The field is saturated: 100+ papers, SOTA 96% (DistilBERT + TF-IDF ensemble [1]), 89% with linguistic features [2], 92.37% RoBERTa ensemble [8]. BloomNet [5] (+POS+NER) and ETFPOS-IDF [3] are closest to multi-signal approaches. The proposed differentiators — ε-tolerance margin and closed-loop verification — have no direct prior art. Mahboob (2026) [4] analyzes classification ambiguity but does not propose ε-tolerance. Yaacoub et al. (2026) [7] does post-hoc verification but not reapplication of signal extractors.

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

**Novelty:** High. Continuous scoring (not binary) + type-aware decomposition + differential redaction (not just blocking) has no prior art combination. Zhao et al. (ACL 2026) [9] evaluate answer leakage robustness with a binary metric — the first paper to define the leakage evaluation task. PEARL [10] uses multi-dimension pedagogical scoring but across 8 general pedagogical traits, not leakage-specific sub-dimensions. EduGuard [11] reports a 9.8% direct-answer leakage rate but uses a single metric. No existing work (a) decomposes answers by type before scoring, (b) applies DP-style structured redaction to educational answer content, or (c) combines continuous scoring with deterministic redaction in a single pipeline. The closest to differential redaction is RE-DACT [69], which applies DP to general structured/unstructured data — not to educational tutoring responses.

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

**Novelty:** Medium-High. TRACE (Shen et al., 2026) [14] audits whether a tutor's reasoning is *answer-driven* via truncated CoT prefix probing — it detects a problem but does not produce structured rationale. ES-LLMs (SafeTutors framework [17]) logs agent decisions as rule-based traces but not as a machine-parseable, schema-enforced pedagogical rationale. ScaffoldLM [15] uses assessment-driven control loops with cognitive state inference but does not expose the rationale as an external artifact. No prior work generates pedagogical rationale as a structured, inspectable output with schema validation and verifiability constraints.

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

Dimensions (proposed — requires IRB or ethics review before implementation): **language** (English vs. code-switching, stored in every request) and **mastery band** (<0.30 / 0.30-0.50 / 0.50-0.70 / ≥0.70). Limited to two dimensions to keep per-cell sample sizes meaningful. Expandable to course-level and topic-level aggregation later if data volume supports it.

**Caveat:** Demographic dimension selection is sensitive. The initial implementation uses non-demographic dimensions (course, topic, mastery band) only. Demographic dimensions (language) require consultation with institutional ethics board before activation.

**Novelty:** High. All existing equity dashboards track *outcomes* (grades, pass rates): Sloan-Lynch & Morse (LAK 2024) [19] built a Course Diversity Dashboard tracking outcome inequities. The CSU Course Equity Portal monitors grade equity gaps. FairTutor [20] tracks *access-tier* equity (premium vs. free AI), not demographic process equity. No existing system tracks whether different student groups receive different AI tutor *response quality* (leakage rate, scaffolding depth, citation rate, Socratic engagement). The Marked Pedagogies study [21] found systematic stereotype-aligned shifts in automated writing feedback — confirming the problem exists but providing no monitoring framework.

### 5.5 Personalized Forgetting Curves

**Files:** `knowledge_state.py` (modify), `deep_kt.py` (reactivate)

**What it does:** Replaces the fixed 0.15 learning rate in `knowledge_state.py:update_state()` with per-student forgetting curve parameters:

- **γᵢ** (decay rate): How fast student i forgets
- **αᵢ** (initial strength): How well student i encodes new information
- **βᵢ** (retrieval threshold): How confident student i needs to be to answer correctly

These are learned as student-specific embeddings via a hypernetwork on top of the existing DKT model in `deep_kt.py`. Parameters update after each quiz interaction.

**Novelty:** Medium. CPF (Wang et al., 2026) [24] personalizes forgetting rates via learned embeddings but not full interpretable parameter estimation. LefoKT (Bai et al., AAAI 2025) [25] decouples forgetting from problem relevance via relative attention. memoryKT (Lin et al., 2025) [26] computes a personalized forgetting score via VAE but does not estimate interpretable parameters. UKT (Cheng et al., AAAI 2025) [23] handles uncertainty but not forgetting parameters. FSRS [27][28] optimizes 19-21 global parameters shared across all students — the most widely deployed forgetting model but with no per-student customization. No existing work learns a complete interpretable parameter set (decay γᵢ, strength αᵢ, threshold βᵢ) per student in a neural KT framework, bridging the FSRS (global optimization) and DKT (deep learning) paradigms.

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

**Novelty:** Low. Query decomposition for RAG is standard practice. Ammann et al. (ACL 2025) [29] showed QD + reranking achieves MRR@10 +36.7% and F1 +11.6% on MultiHop-RAG. Petcu et al. (EACL 2026) [30] formulated QD as an exploration-exploitation bandit problem. ToR-Lite [31] eliminates LLM calls during decomposition entirely. UniRAG [32] and QDRAG (AAAI 2026) [33] both integrate QD with iterative reasoning and citation. Shaikh et al. (2026) [34] conducted a controlled ablation showing QD contributes +1.4 EM (p=0.004) on 5K HotpotQA questions. Paper angle is a lecture-scoped ablation study, not a novel method.

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

### Phase 0: Setup

**Goal:** Establish baseline before feature work.

| Step | Detail | Effort |
|------|--------|--------|
| 0.1 | Set `JWT_SECRET` in `backend/.env` to a real random value (currently `change_this_to_a_random_secret`) | 5 min |
| 0.2 | Enable `GATEKEEPER_ENABLED=true` in `backend/app/config.py` (currently `false` for dev) | 5 min |
| 0.3 | Run existing test suite: `cd backend && pytest tests/ -v` — establish baseline pass/fail | 10 min |
| 0.4 | Run ruff: `cd backend && ruff check .` — establish baseline lint state | 5 min |
| 0.5 | Ensure repo is private until provisional patent filings are complete | — |

### Phase 1: Patent Foundation (Priority: High)

**Goal:** Build enough to file 3 provisional patents. Repo remains private until filings complete.

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

| # | Title | Type | Filing Window | Key Claims |
|---|-------|------|--------------|------------|
| P1 | "System and Method for Type-Aware Answer Decomposition and Differential Redaction for Leakage Prevention in AI Tutoring" | Indian Provisional | Before any public code push | (a) Type-aware decomposition of expected answers into structural categories; (b) Continuous multi-dimensional leakage scoring with weighted sub-dimensions; (c) Category-specific differential redaction rules with configurable severity thresholds; (d) Tiered similarity-based gating (embedding → LLM → block) |
| P2 | "Method for Generating and Validating Structured Pedagogical Rationale Traces in AI Tutoring Systems" | Indian Provisional | Within 6 months of P1 | (a) Schema-enforced structured rationale trace generation as part of the response pipeline; (b) Machine-parseable pedagogical decision log with strategy selection and avoidance reasons; (c) Verifiability constraints ensuring trace claims match actual student state |
| P3 | "System for Demographic-Stratified Monitoring of AI Tutoring Process Quality" | Indian Provisional | Within 6 months of P1 | (a) Process quality metrics aggregated by demographic dimension (not outcome metrics); (b) Automated alerting on statistically significant disparities in leakage rate, scaffolding depth, or citation quality; (c) Privacy-preserving aggregation with minimum sample size thresholds |

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

---

## 12. References

### Bloom's Taxonomy Classification
[1] A. Alammary and S. Masoud, "Towards Smarter Assessments: Enhancing Bloom's Taxonomy Classification with a Bayesian-Optimized Ensemble Model Using Deep Learning and TF-IDF Features," *Electronics*, vol. 14, no. 12, art. 2312, 2025. DOI: 10.3390/electronics14122312.

[2] J. P. Tonde and S. Sankaye, "Ensemble-Based Question Classification Using Bloom's Taxonomy," in *Proc. IEEE IDICAIHEI*, 2025. DOI: 10.1109/idicaihei65991.2025.11377635.

[3] M. O. Gani, R. K. Ayyasamy, S. M. Alhashmi, A. Sangodiah, and Y. T. Fui, "ETFPOS-IDF: A Novel Term Weighting Scheme for Examination Question Classification Based on Bloom's Taxonomy," *IEEE Access*, vol. 10, pp. 132777–132785, 2022. DOI: 10.1109/ACCESS.2022.3230592.

[4] M. Mahboob, "Misclassification Analysis in Automated Bloom's Taxonomy Classifiers: A Data-Centric Perspective on Educational Software," *ICCK J. Softw. Eng.*, vol. 2, no. 2, pp. 138–155, 2026. DOI: 10.62762/JSE.2026.118512.

[5] A. Waheed, M. Goyal, N. Mittal, D. Gupta, A. Khanna, and M. Sharma, "BloomNet: A Robust Transformer based Model for Bloom's Learning Outcome Classification," in *Proc. ICNLSP*, Trento, Italy, 2021, pp. 209–218. [Online]. Available: https://aclanthology.org/2021.icnlsp-1.24/.

[6] A. Maharramov, "Automatic Classification of Questions According to Bloom Taxonomy," M.S. thesis, NOVA Univ. Lisbon, 2025. URI: http://hdl.handle.net/10362/190079.

[7] A. Yaacoub, Z. Assaghir, A. Kar, and J. Da-Rugna, "From Generation to Certification: A Framework for Explainable and Taxonomy-Aware AI in Educational Assessment," in *Proc. CSEDU*, 2026.

[8] M. M. Hamid et al., "Enhancing Educational Assessment through Automated Question Classification Using a RoBERTa-Based Ensemble Model," *Sci. Rep.*, 2026. DOI: 10.1038/s41598-026-45486-1.

### Answer Leakage & Integrity
[9] J. Zhao, M. Knežević, and T. Käser, "Evaluating Answer Leakage Robustness of LLM Tutors against Adversarial Student Attacks," in *Proc. ACL*, 2026, pp. 30588–30617. DOI: 10.18653/v1/2026.acl-long.1412.

[10] Q. Chang et al., "PEARL: Training Socratic Tutors with Pedagogically Aligned Reinforcement Learning," arXiv:2605.29582, 2026.

[11] S. M. A. Hossain, R. K. Shayoni, M. F. Mridha, and J. Shin, "EduGuard: A Safe RAG-Based LLM Tutor for Programming Education," arXiv:2607.15738, 2026.

[12] S. Zhao, K. Yu, Y. Yuan, P. He, and H. Wen, "SHAPE: Unifying Safety, Helpfulness and Pedagogy for Educational LLMs," in *Proc. ACL*, 2026, pp. 11537–11553. DOI: 10.18653/v1/2026.acl-long.529.

[13] J. Shao, Q. Wu, H. Zhang, S. Sun, and J. Zhuang, "Mitigating Scaffolding Collapse in Socratic Tutors via Representation Alignment," arXiv:2607.19371, 2026.

[14] B. Shen, D. Shang, Y. Wang, and T. Ning, "Detecting Answer-Driven Reasoning in LLM-Based Educational Tutors via Truncated Chain-of-Thought Auditing," arXiv:2607.04572, 2026.

[15] Z. Li, Q. Zhu, M. Wang, J. Li, and H. Huang, "Planning-Guided Tutoring with Assessment-Driven Memory for Pedagogical LLM Tutors," in *Proc. ACL*, 2026, pp. 7165–7188. DOI: 10.18653/v1/2026.acl-long.325.

[16] D. Dinucu-Jianu, J. Macina, N. Daheim, I. Hakimi, I. Gurevych, and M. Sachan, "From Problem-Solving to Teaching Problem-Solving: Aligning LLMs with Pedagogy using Reinforcement Learning," in *Proc. EMNLP*, 2025, pp. 272–292. DOI: 10.18653/v1/2025.emnlp-main.15.

[17] R. Hazra et al., "SafeTutors: Benchmarking Pedagogical Safety in AI Tutoring Systems," arXiv:2603.17373, 2026.

### Equity & Fairness
[18] A. Gupta, N. Patil, S. Ghosh, and S. S. Gaikwad, "Compounding Disadvantage: Auditing Intersectional Bias in LLM-Generated Explanations Across Indian and American STEM Education," in *Proc. ACM FAccT*, 2026. DOI: 10.1145/3805689.3812394.

[19] J. K. Sloan-Lynch and R. Morse, "Equity-Forward Learning Analytics: Designing a Dashboard to Support Marginalized Student Success," in *Proc. LAK*, Kyoto, Japan, 2024. DOI: 10.1145/3636555.3636844.

[20] Q. Xu, "FairTutor: Equity-Aware Pedagogical LLM Routing for Budget-Constrained AI Tutoring," in *AI4EDU @ KDD*, Jeju, Korea, 2026.

[21] M. Tan, L. Phalen, and D. Demszky, "Marked Pedagogies: Examining Linguistic Biases in Personalized Automated Writing Feedback," in *Proc. LAK*, 2026. DOI: 10.1145/3785022.3785113.

[22] A. Vinodh et al., "Evaluating an AI Tutor for Bias Across Different Foundation Models," in *Proc. AIED*, 2025. DOI: 10.1007/978-3-031-98465-5_4.

### Knowledge Tracing & Forgetting
[23] W. Cheng et al., "Uncertainty-aware Knowledge Tracing," in *Proc. AAAI*, vol. 39, no. 27, pp. 27905–27913, 2025. DOI: 10.1609/aaai.v39i27.35007.

[24] S. Wang et al., "Personalized Forgetting Mechanism with Concept-Driven Knowledge Tracing," *ACM*, 2026. DOI: 10.1145/3810940.

[25] Y. Bai, X. Li, Z. Liu, Y. Huang, M. Tian, and W. Luo, "Rethinking and Improving Student Learning and Forgetting Processes for Attention based Knowledge Tracing Models," in *Proc. AAAI*, vol. 39, no. 27, pp. 27822–27830, 2025. DOI: 10.1609/aaai.v39i27.34998.

[26] M. Lin, K. Deng, Z. Wu, Z. Zheng, and J. Li, "MemoryKT: An Integrative Memory-and-Forgetting Method for Knowledge Tracing," arXiv:2508.08122, 2025.

[27] J. Ye, J. Su, and Y. Cao, "A Stochastic Shortest Path Algorithm for Optimizing Spaced Repetition Scheduling," in *Proc. KDD*, 2022, pp. 4381–4390. DOI: 10.1145/3534678.3539081.

[28] J. Ye, J. Su, S. Nie, Y. Cao, and Y. Chen, "Optimizing Spaced Repetition Schedule by Capturing the Dynamics of Memory," *IEEE Trans. Knowl. Data Eng.*, vol. 35, no. 10, pp. 10085–10097, 2023. DOI: 10.1109/TKDE.2023.3251721.

### Query Decomposition
[29] P. J. L. Ammann, J. Golde, and A. Akbik, "Question Decomposition for Retrieval-Augmented Generation," in *Proc. ACL Student Research Workshop*, Vienna, Austria, 2025, pp. 497–507. DOI: 10.18653/v1/2025.acl-srw.32.

[30] R. Petcu et al., "Query Decomposition for RAG: Balancing Exploration-Exploitation," in *Proc. EACL*, Rabat, Morocco, 2026, pp. 6857–6871. DOI: 10.18653/v1/2026.eacl-long.322.

[31] X. Chen et al., "ToR-Lite: A Lightweight Semantic Query Decomposition for Multi-Hop Retrieval-Augmented Generation in Cloud-Based AI Systems," *Applied Sciences*, vol. 16, no. 8, art. 3966, 2026. DOI: 10.3390/app16083966.

[32] G. I. Kim, J. W. Kim, and B. Jang, "UniRAG: A Unified RAG Framework for Knowledge-Intensive Queries with Decomposition, Break-Down Reasoning, and Iterative Rewriting," in *Proc. EMNLP Findings*, 2025.

[33] Y. Wang et al., "Faithful in Steps: Improving Generalization and Citation in RAG via Query Decomposition," in *Proc. AAAI*, Singapore, 2026, pp. 35671–35679.

[34] S. Shaikh et al., "Dissecting Agentic RAG: A Component Ablation for Multi-Hop QA with a Local 7B Model," arXiv:2606.21553, 2026.

### Multi-Agent & Dialogue
[35] Y. Li et al., "KELE: A Consultant-Teacher Dual-Agent Framework for Knowledge-Enhanced Learning," in *Proc. EMNLP*, 2025.

[36] A. Kumar et al., "IntelliCode: Multi-Agent LLM Framework for Interactive Code Generation and Tutoring," in *Proc. EACL*, 2026.

[37] S. Das et al., "BIPED: A Framework for Dialogue Act Prediction in Pedagogical Conversations," in *Proc. ACL*, 2024.

[38] Z. Wang, Z. Lu, C. Zeng, S. Dong, M. Zuo, and J. Sun, "MMKT: Multimodal Knowledge Tracing in Personalized E-Learning Systems," *IEEE Trans. Comput. Soc. Syst.*, vol. 12, no. 6, pp. 5179–5198, 2025. DOI: 10.1109/TCSS.2025.3574663.

[39] A. Rumble et al., "LEA: A Tri-Modal Agent Framework for Classroom Deployment of AI Tutors," arXiv:2607.13370, 2026.

[40] W. Han et al., "Contrastive Cross-Course Knowledge Tracing via Concept Graph Guided Knowledge Transfer," in *Proc. IJCAI*, 2025, pp. 7401–7409. DOI: 10.24963/ijcai.2025/823.

[41] M. Deng et al., "ACKT: Adversarial Cross-Domain Knowledge Tracing for Cold-Start Scenarios," in *Proc. WWW*, 2026.

[42] A. Alrabah et al., "InstructKG: A 5-Stage Pipeline for Automatic Knowledge Graph Construction from Lecture PDFs," GitHub, 2025. [Online]. Available: https://github.com/aalrabah/instructkg.

[43] R. Alatrash et al., "CourseMapper: Unsupervised Multi-Criteria Prerequisite Inference from PDF Documents," arXiv:2509.05393, 2025.

[44] A. Scarlatos et al., "LLMKT: Fine-Tuning Large Language Models for Knowledge Tracing from Dialogue," in *Proc. LAK*, 2025.

[45] Z. Jia et al., "DiaCDM: Cognitive Diagnosis in Teacher-Student Dialogues Using IRE Framework and AMR Graphs," in *Proc. ACL*, 2025.

### Assessment & Generation
[46] I. Amanlou et al., "KNIGHT: A Reusable Knowledge Graph for Difficulty-Controlled MCQ Generation," in *Proc. AAAI*, 2026.

[47] R. Zhang et al., "KAQG: Knowledge-Enhanced Automatic Question Generation with Difficulty Control," in *Proc. EMNLP*, 2025.

[48] Z. Wang et al., "CLAF: Adaptive Explanation Generation via Hierarchical Knowledge Graph Retrieval and Preference Learning," in *Proc. EMNLP*, 2025.

[49] A. Robrecht et al., "SNAPE-PM: Bayesian Partner Modeling for Adaptive Tutoring," in *Proc. AIED*, 2025.

[50] X. Liu et al., "MetaCLASS: Metacognitive Tutoring with 11 Interpretable Coach Moves," in *Proc. AAAI*, 2026.

[51] Z. Chen et al., "MC-CPO: Mastery-Conditioned Constrained Policy Optimization for Safe Tutoring," in *Proc. AAAI*, 2026.

[52] Y. Huang et al., "MWO: Multi-Objective Curriculum Sequencing via Memetic Optimization," in *Proc. EDM*, 2025.

[53] Y. Zhang et al., "GapProbe: Counterfactual Question Generation for Knowledge Gap Detection," in *Proc. AAAI*, 2026.

[54] M. Fateen et al., "RAG-Based Automated Short-Answer Scoring with Citation-Backed Feedback," in *Proc. BEA Workshop @ ACL*, 2024.

### Evaluation & Quality
[55] S. Maurya et al., "MRBench: A Multi-Dimension Evaluation Benchmark for Math Reasoning in AI Tutors," in *Proc. ACL*, 2025.

[56] BEA 2025 Shared Task, "Evaluating Pedagogical Quality in AI-Generated Tutoring Responses," in *Proc. BEA Workshop @ ACL*, 2025.

[57] J. Lee et al., "QuizWeaver: Deterministic Bloom's and Webb's DOK Alignment for Automated Assessment Generation," GitHub, 2026.

[58] R. Singh et al., "Curriculum Cartographer: LLM-Based Mapping of Artifacts to Learning Outcomes with Bloom's Classification," in *Proc. CSEDU*, 2026.

[59] Y. Liu et al., "MSCL: Self-Supervised Graph Contrastive Learning for Knowledge Tracing," in *Proc. AAAI*, 2026.

[60] Z. Wang et al., "Coral: Collaborative Cognitive Diagnosis with Disentangled Representation Learning," in *Proc. EDM*, 2024.

[61] T. Kim et al., "MiRAGE: Retrieval-Guided Multi-Stage Reasoning for Misconception Detection," in *Proc. ACL*, 2025.

[62] Y. Chen et al., "Cognitive-Uncertainty Guided Knowledge Distillation for Misconception Detection," in *Proc. ACL*, 2026.

[63] L. Zhang et al., "MHPO: Multi-Horizon Preference Optimization for Pedagogical Strategy Selection," in *Proc. ACL*, 2026.

[64] A. Hazra et al., "EduGuardBench: A Benchmark for Evaluating Pedagogical Fidelity and Safety in AI Tutors," in *Proc. AAAI*, 2026.

[65] S. Yang et al., "EDF: An Evidence-Decision-Feedback Framework for Dialogue Act Scaffolding in AI Tutoring," in *Proc. AAAI*, 2026.

[66]

[67]

[68]

[69] S. Choudhary et al., "RE-DACT: A Differential Privacy and Redaction Framework for Structured and Unstructured Data," in *Proc. USENIX Security*, 2025.
