# Implementation Plan: Integrity Enforcement + Multi-Signal Bloom's Detector

**13 independent steps across 2 phases.** Each step lists: files touched, test strategy, and done condition. Steps within a phase can be parallelized across branches.

---

## Phase 1 — Integrity & Leakage Enforcement (Steps 1–7)

---

### Step 1 — Config flags + DB table
**Files:** `backend/app/config.py`, `backend/app/db.py`
**Can parallelize with:** Step 2, 3, 4

**`config.py` — after `QUERY_ENHANCER_NUM_QUERIES` (line 69):**
```python
INTEGRITY_ENABLED: bool = os.getenv("INTEGRITY_ENABLED", "false").lower() == "true"
LEAKAGE_THRESHOLD: float = float(os.getenv("LEAKAGE_THRESHOLD", "0.7"))
```

**`db.py` — in `_init_schema`, insert before `DEFINE TABLE IF NOT EXISTS knowledge_state` (line 237):**
```sql
DEFINE TABLE IF NOT EXISTS integrity_log SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS course_code ON TABLE integrity_log TYPE string;
DEFINE FIELD IF NOT EXISTS query ON TABLE integrity_log TYPE string;
DEFINE FIELD IF NOT EXISTS answer_type ON TABLE integrity_log TYPE string;
DEFINE FIELD IF NOT EXISTS leakage_score ON TABLE integrity_log TYPE float;
DEFINE FIELD IF NOT EXISTS leakage_directness ON TABLE integrity_log TYPE float;
DEFINE FIELD IF NOT EXISTS leakage_procedural ON TABLE integrity_log TYPE float;
DEFINE FIELD IF NOT EXISTS leakage_completeness ON TABLE integrity_log TYPE float;
DEFINE FIELD IF NOT EXISTS leakage_specificity ON TABLE integrity_log TYPE float;
DEFINE FIELD IF NOT EXISTS redacted ON TABLE integrity_log TYPE bool;
DEFINE FIELD IF NOT EXISTS original_response ON TABLE integrity_log TYPE string;
DEFINE FIELD IF NOT EXISTS redacted_response ON TABLE integrity_log TYPE option<string>;
DEFINE FIELD IF NOT EXISTS timestamp ON TABLE integrity_log TYPE datetime DEFAULT time::now();
DEFINE INDEX IF NOT EXISTS integrity_log_course_idx ON TABLE integrity_log FIELDS course_code;
```

**Tests:** Assert config parses. Assert DDL runs without error in `_init_schema`.

**Done:** Backend starts, `/health` returns 200. No behavioral change (`INTEGRITY_ENABLED=false`).

---

### Step 2 — `answer_decomposer.py` (standalone module)
**New file:** `backend/app/answer_decomposer.py`
**Can parallelize with:** Step 3, 4

```python
from enum import Enum

class AnswerType(str, Enum):
    NUMERIC = "numeric"
    CODE = "code"
    PROOF = "proof"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"

_atype_cache: dict[str, AnswerType] = {}

async def classify_answer_type(query: str) -> AnswerType:
    """Regex classifier (fast path) → AnswerType.
       Patterns:
         'how many|calculate|what is \\d+' → NUMERIC
         'write.*code|implement|function|def ' → CODE
         'prove|show that|derive' → PROOF
         'define|what is|list|name|state' → SHORT_ANSWER
         else → ESSAY
       Cached in _atype_cache by query hash.
    """

async def extract_answer_core(query: str, answer_type: AnswerType) -> str:
    """Strip question framing, return core noun phrase.
       E.g. 'What is the time complexity of quicksort?' → 'the time complexity of quicksort'.
       Regex: remove leading WH-word + verb, keep rest.
    """
```

**Tests:** `tests/test_answer_decomposer.py`
- `test_classify_numeric` — "Calculate 5 + 3" → NUMERIC
- `test_classify_code` — "Write a Python function to sort" → CODE
- `test_classify_proof` — "Prove that √2 is irrational" → PROOF
- `test_classify_short` — "What is a binary tree" → SHORT_ANSWER
- `test_classify_essay` — "Discuss the impact of AI on education" → ESSAY
- `test_cache_hit` — same query returns cached type
- `test_extract_core_short` — "What is X?" → "X"
- `test_extract_core_code` — "Write a function to sort" → "function to sort"

**Done:** `pytest tests/test_answer_decomposer.py -v` passes. No backend edits needed.

---

### Step 3 — `leakage_scorer.py` (standalone module)
**New file:** `backend/app/leakage_scorer.py`
**Can parallelize with:** Step 2, 4

```python
from dataclasses import dataclass
from app.answer_decomposer import AnswerType

@dataclass
class LeakageScore:
    overall: float
    directness: float
    procedural_reveal: float
    completeness: float
    specificity: float

async def compute_leakage(
    answer_core: str,
    response: str,
    chunks: list[dict],
    answer_type: AnswerType,
) -> LeakageScore:
    """Multi-dimensional leakage assessment:
       directness       = cosine_sim(embed(answer_core), embed(response))
       procedural_reveal = step-indicator tokens count / total sentences
       completeness     = max overlap of chunk topics mentioned in response
       specificity      = per-type: numeral count, code ratio, connective tokens, key-term density
       overall          = weighted average of 4 sub-scores
    """
```

**Tests:** `tests/test_leakage_scorer.py`
- Mock `router.embed_text` to return known vectors; assert directness matches cosine
- Test each answer_type-specific heuristic independently (numeric→count digits, code→count code fences, proof→count therefore/hence/shows)
- Edge: empty response, single word, exact match, response 10x longer than typical

**Done:** `pytest tests/test_leakage_scorer.py -v` passes. No backend edits.

---

### Step 4 — `differential_redactor.py` (pure function)
**New file:** `backend/app/differential_redactor.py`
**Can parallelize with:** Step 2, 3

```python
from app.answer_decomposer import AnswerType
from app.leakage_scorer import LeakageScore

async def redact_response(
    response: str,
    score: LeakageScore,
    answer_type: AnswerType,
    threshold: float = 0.7,
) -> str:
    """Type-aware redaction when score.overall > threshold:
       NUMERIC → re.sub(r'\\b\\d+\\b', '[REDACTED_VALUE]', response)
       CODE    → keep first + last line, replace body with '# ... [solution redacted]'
       PROOF   → remove sentences after 'Therefore' / 'Thus' / 'Hence' / 'Consequently'
       SHORT_ANSWER → remove sentence with highest cosine to answer_core
       ESSAY   → remove the sentence with highest claim density
       No-op if score <= threshold.
    """
```

**Tests:** `tests/test_differential_redactor.py`
- Each answer_type: known leakage_score above threshold → redaction fires correctly
- Below-threshold score (all types) → no-op
- Edge: score.overall > threshold but no redactable pattern found (e.g., NUMERIC with no digits) → return response unchanged

**Done:** `pytest tests/test_differential_redactor.py -v` passes.

---

### Step 5 — `integrity_enforcer.py` (orchestrator)
**New file:** `backend/app/integrity_enforcer.py`
**Depends on:** Steps 2, 3, 4

```python
from app.answer_decomposer import classify_answer_type, extract_answer_core
from app.leakage_scorer import compute_leakage, LeakageScore
from app.differential_redactor import redact_response
from app.config import settings
from app.db import get_db

class IntegrityEnforcer:
    async def enforce(
        self,
        query: str,
        response: str,
        chunks: list[dict],
        course_code: str,
    ) -> tuple[str, LeakageScore | None, bool]:
        """Returns (final_response, score_or_None, was_redacted)."""
        if not settings.INTEGRITY_ENABLED:
            return response, None, False

        atype = await classify_answer_type(query)
        answer_core = await extract_answer_core(query, atype)
        score = await compute_leakage(answer_core, response, chunks, atype)
        was_redacted = score.overall > settings.LEAKAGE_THRESHOLD
        final = await redact_response(response, score, atype, settings.LEAKAGE_THRESHOLD) if was_redacted else response
        await self._log(query, course_code, atype, score, was_redacted, response, final)
        return final, score, was_redacted

    async def _log(self, query: str, course_code: str, atype: AnswerType,
                   score: LeakageScore, redacted: bool,
                   original: str, final: str) -> None:
        if not settings.INTEGRITY_ENABLED:
            return
        db = await get_db()
        await db.query(
            "CREATE integrity_log CONTENT { course_code: $cc, query: $q, answer_type: $at, "
            "leakage_score: $ls, leakage_directness: $ld, leakage_procedural: $lp, "
            "leakage_completeness: $lc, leakage_specificity: $lsp, redacted: $r, "
            "original_response: $o, redacted_response: $rf, timestamp: time::now() }",
            {"cc": course_code, "q": query, "at": atype.value, "ls": score.overall,
             "ld": score.directness, "lp": score.procedural_reveal, "lc": score.completeness,
             "lsp": score.specificity, "r": redacted, "o": original,
             "rf": final if redacted else None},
        )

integrity = IntegrityEnforcer()
```

**Tests:** `tests/test_integrity_enforcer.py`
- Mock `classify_answer_type`, `extract_answer_core`, `compute_leakage`, `redact_response`
- Assert `enforce()` calls all 3 sub-steps in correct order
- Assert DB write is called with expected values
- Assert short-circuit when `INTEGRITY_ENABLED=false`

**Done:** `pytest tests/test_integrity_enforcer.py -v` passes.

---

### Step 6 — Wire into `query_engine.py`
**File:** `backend/app/query_engine.py` — 2 insertion points + 1 import

```python
# Line 18, after "from app.verifier import verifier":
from app.integrity_enforcer import integrity

# In query_stream() — after line 332 (the certification note yield), before line 333:
        redacted, leak_score, was_redacted = await integrity.enforce(
            query, full_response, chunks, course_code,
        )
        if was_redacted:
            full_response = redacted
            yield {"type": "content", "content": "\n\n_Some content was redacted to prevent answer leakage._"}

# In query() — after line 413, before line 415:
        redacted, leak_score, was_redacted = await integrity.enforce(
            query, response_text, chunks, course_code,
        )
        if was_redacted:
            response_text = redacted
```

**Tests:**
- With `INTEGRITY_ENABLED=false` (default): all existing `pytest tests/test_rag.py -v` pass
- With `INTEGRITY_ENABLED=true`: integration test sends query, asserts metadata

**Done:** Backend starts without error. `INTEGRITY_ENABLED=false` preserves existing behavior.

---

### Step 7 — Phase 1 E2E tests (can be skipped by default)
**New file:** `tests/test_integrity_e2e.py`

```python
# All tests marked with @pytest.mark.skipif(True, ...) like test_e2e_pipeline.py
# Requires running SurrealDB + INTEGRITY_ENABLED=true
```

- NUMERIC redaction: "Calculate 5 * 3" → response contains `[REDACTED_VALUE]`
- CODE redaction: "Write bubble sort in Python" → code body replaced
- Below-threshold: `LEAKAGE_THRESHOLD=1.0` → no redaction
- integrity_log row created in DB

**Done:** `pytest tests/test_integrity_e2e.py -v` passes with SurrealDB.

---

## Phase 2 — Multi-Signal Bloom's Detector (Steps 8–13)

---

### Step 8 — Config flags
**File:** `backend/app/config.py`
**Can run any time, even before Phase 1**

```python
# After BLOOM_VALIDATION_ENABLED (line 67):
BLOOM_SIGNALS_ENABLED: bool = os.getenv("BLOOM_SIGNALS_ENABLED", "false").lower() == "true"
BLOOM_EPSILON: float = float(os.getenv("BLOOM_EPSILON", "0.05"))
```

**Done:** Backend starts. Feature is dark.

---

### Step 9a — `bloom_signals.py` (rule-based extractors)
**New file:** `backend/app/bloom_signals.py`
**Can parallelize with:** Step 9b, 10

```python
import re

BLOOM_VERBS = {
    1: {"define", "list", "name", "state", "recall", "identify", "label"},
    2: {"explain", "summarize", "interpret", "describe", "paraphrase", "illustrate"},
    3: {"apply", "solve", "use", "implement", "calculate", "demonstrate", "show"},
    4: {"analyze", "compare", "contrast", "differentiate", "examine", "categorize"},
    5: {"evaluate", "judge", "critique", "justify", "defend", "assess", "argue"},
    6: {"design", "create", "construct", "invent", "develop", "generate", "compose"},
}

async def verb_taxonomy_signal(query: str) -> float:
    """POS-tag verbs (nltk), match against BLOOM_VERBS.
       Returns bloom level 1-6 or 0.

async def syntactic_complexity_signal(query: str) -> float:
    """Clause count via regex (',', 'and', 'which', 'that').
       Map: 1 clause → L1, 2 → L2, 3-4 → L3-4, 5+ → L5-6.

async def interrogative_type_signal(query: str) -> float:
    """question_start_re = {
        r'^(what|who|when|where|list|define)'       -> L1,
        r'^(explain|describe|summarize|what.*mean)'  -> L2,
        r'^(how|apply|use|solve|calculate)'          -> L3,
        r'^(compare|contrast|analyze|difference)'    -> L4,
        r'^(evaluate|judge|justify|critique|assess)' -> L5,
        r'^(design|create|develop|construct|propose)'> L6,
    }

async def presupposition_structure_signal(query: str) -> float:
    """Count triggers: 'assuming', 'given that', 'suppose', 'if.*then', 'consider'.
       0 -> 0, 1-2 -> L4, 3+ -> L5/6.

async def referential_scope_signal(query: str) -> float:
    """Count capitalized nouns / multi-word entities (regex).
       0-1 -> L1-2, 2-3 -> L3-4, 4+ -> L5-6.
```

**Tests:** `tests/test_bloom_signals.py`
- Each signal tested independently with known inputs
- Edge: empty query, single word, code, all caps

**Done:** `pytest tests/test_bloom_signals.py -v` passes.

---

### Step 9b — `bloom_signals.py` (LLM signal + gather)
**File:** `backend/app/bloom_signals.py` (append)
**Can parallelize with:** Step 10

```python
async def predicted_answer_type_signal(query: str) -> float:
    """Call classify_answer_type(query) from answer_decomposer.
       Map AnswerType → bloom level (returned as float):
         AnswerType.NUMERIC       -> 3.0   (Apply)
         AnswerType.CODE          -> 3.0   (Apply)
         AnswerType.PROOF         -> 4.0   (Analyze)
         AnswerType.SHORT_ANSWER  -> 1.0   (Remember)
         AnswerType.ESSAY         -> 5.0   (Evaluate)

async def compute_all_signals(query: str) -> list[float]:
    """Run all 6 via asyncio.gather, return [s1..s6]."""
    return await asyncio.gather(
        verb_taxonomy_signal(query),
        syntactic_complexity_signal(query),
        interrogative_type_signal(query),
        referential_scope_signal(query),
        presupposition_structure_signal(query),
        predicted_answer_type_signal(query),
    )
```

**Tests:** `predicted_answer_type_signal` with mock. `compute_all_signals` returns 6 floats.

**Done:** All 6 signals return values in [0, 1].

---

### Step 10 — `bloom_fusion.py`
**New file:** `backend/app/bloom_fusion.py`
**Can parallelize with:** Step 11

```python
import numpy as np

# Expert-heuristic starting values. Calibrate after labeled dataset.
INITIAL_WEIGHTS: np.ndarray = np.array([
    # V    S    I    R    P    A   ← signal indices
    [.4,  .1,  .3,  .05, .05, .1],  # Remember
    [.3,  .15, .3,  .1,  .05, .1],  # Understand
    [.2,  .2,  .25, .15, .1,  .1],  # Apply
    [.1,  .2,  .15, .25, .2,  .1],  # Analyze
    [.05, .15, .1,  .2,  .3,  .2],  # Evaluate
    [.05, .1,  .1,  .15, .2,  .4],  # Create
])

async def fuse_signals(signals: list[float], epsilon: float = 0.05) -> tuple[int, float]:
    """signals: [s1..s6] each in [0,1]
       Returns (bloom_level 1-6, confidence).
       Weighted sum per level → softmax → argmax.
       If runner-up within epsilon of winner, return 0 (uncertain → LLM fallback).
    """
    s = np.array(signals)
    scores = INITIAL_WEIGHTS @ s
    exp_s = np.exp(scores - np.max(scores))
    probs = exp_s / exp_s.sum()
    ranked = np.argsort(probs)[::-1]
    if len(ranked) >= 2 and (probs[ranked[0]] - probs[ranked[1]]) < epsilon:
        return 0, float(probs[ranked[0]])
    return int(ranked[0]) + 1, float(probs[ranked[0]])
```

**Tests:** `tests/test_bloom_fusion.py`
- Known signal vectors produce expected levels
- Two close scores within epsilon → return 0
- Edge: all-zero signals, all-max signals

**Done:** `pytest tests/test_bloom_fusion.py -v` passes.

---

### Step 11 — `bloom_verifier.py`
**New file:** `backend/app/bloom_verifier.py`
**Can parallelize with:** Step 10

```python
from app.provider_router import router as client

async def verify_bloom_response(response: str, expected_level: int) -> tuple[bool, int]:
    """One LLM call: 'What Bloom level does this response operate at? Answer 1-6.'
       Returns (matches_expected, actual_level).
       On parse failure: return (True, expected_level) — graceful degradation.
    """
    messages = [
        {"role": "system", "content": "You are a Bloom's Taxonomy classifier. "
         "Given a tutor's response to a student, determine the Bloom cognitive level "
         "the response operates at. Return ONLY a single integer 1-6."},
        {"role": "user", "content": f"Response: {response[:1000]}"},
    ]
    raw = await client.chat(messages, temperature=0.1, max_tokens=5)
    try:
        level = int(raw.strip())
        if 1 <= level <= 6:
            return level == expected_level, level
    except (ValueError, TypeError):
        pass
    return True, expected_level
```

**Tests:** Mock `client.chat`. Assert correct matching. Edge: non-numeric LLM response.

**Done:** `pytest tests/test_bloom_verifier.py -v` passes.

---

### Step 12 — Refactor `bloom_classifier.py`
**File:** `backend/app/bloom_classifier.py`

Replace body of `classify_bloom_level`:

```python
from app.bloom_signals import compute_all_signals
from app.bloom_fusion import fuse_signals
from app.config import settings

async def classify_bloom_level(question: str) -> int | None:
    cached = _bloom_cache.get(question)
    if cached is not None:
        return cached

    if settings.BLOOM_SIGNALS_ENABLED:
        signals = await compute_all_signals(question)
        level, confidence = await fuse_signals(signals, settings.BLOOM_EPSILON)
        if level != 0:
            _bloom_cache[question] = level
            return level
        # fall through to LLM fallback

    # existing LLM call (unchanged)
    try:
        response = await client.chat(...)
        ...
    except:
        return None

# Keep classify_bloom_levels() unchanged — it calls classify_bloom_level per question.

async def resolve_from_signals(question: str) -> int | None:
    """Public entry point for query_engine Stage 0."""
    return await classify_bloom_level(question)
```

**Tests:**
- `BLOOM_SIGNALS_ENABLED=false` → existing LLM fallback
- `BLOOM_SIGNALS_ENABLED=true` + confident → signals used, LLM not called
- `BLOOM_SIGNALS_ENABLED=true` + epsilon triggers → LLM fallback called

**Done:** New and existing bloom tests pass.

---

### Step 13 — Wire Stage 0 into `query_engine.py`
**File:** `backend/app/query_engine.py`

```python
# Add to imports:
from app.bloom_classifier import resolve_from_signals

# Add helper method to QueryEngine:
    async def _resolve_bloom_level(self, query: str, existing: int | None) -> int | None:
        if existing is not None or not settings.BLOOM_SIGNALS_ENABLED:
            return existing
        return await resolve_from_signals(query)

# In query_stream() — after line 247 (course_ctx = ...), before line 249 (gatekeeper.check_and_enrich):
        # ── Stage 0: Multi-Signal Bloom's Detector ──
        bloom_level = await self._resolve_bloom_level(query, bloom_level)

# In query() — after line 358 (course_ctx = ...), before line 359 (gatekeeper.check_and_enrich):
        bloom_level = await self._resolve_bloom_level(query, bloom_level)
```

**Tests:** With `BLOOM_SIGNALS_ENABLED=false` → existing tests pass identically.

---

## Parallelization Strategy

```
Branch A: Step 1 → Step 2 → Step 3 → Step 4 → Step 5 → Step 6
Branch B: Step 8 → Step 9a → Step 9b → Step 10 → Step 11 → Step 12 → Step 13
Branch C: Step 7 (after A merges)
```

- Merge A first, then B. Step 7 is optional E2E.
- Steps 1 and 8 touch config.py — no conflicting lines (different insertion points).
- Steps 6 and 13 both touch query_engine.py but modify different lines (Stage 8 at line 332, Stage 0 at line 247) — no conflict.

---

## Done Conditions Summary

| Step | Done when |
|------|-----------|
| 1 | Backend starts, `/health` 200 |
| 2 | `pytest tests/test_answer_decomposer.py -v` passes |
| 3 | `pytest tests/test_leakage_scorer.py -v` passes |
| 4 | `pytest tests/test_differential_redactor.py -v` passes |
| 5 | `pytest tests/test_integrity_enforcer.py -v` passes |
| 6 | `pytest tests/test_rag.py -v` passes (existing) |
| 7 | `pytest tests/test_integrity_e2e.py -v` passes (with SurrealDB) |
| 8 | Backend starts, `/health` 200 |
| 9a | `pytest tests/test_bloom_signals.py -v` passes |
| 9b | All 6 signals return [0,1] |
| 10 | `pytest tests/test_bloom_fusion.py -v` passes |
| 11 | `pytest tests/test_bloom_verifier.py -v` passes |
| 12 | Bloom tests pass, LLM fallback works |
| 13 | `pytest tests/test_rag.py -v` passes (existing), backend starts |
