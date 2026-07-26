# Integrity & Leakage Enforcement + Multi-Signal Bloom's Detector — Implementation Plan

---

## Phase 1 — Integrity & Leakage Enforcement

### 1. `answer_decomposer.py` — Function Signatures

```python
from enum import Enum

class AnswerType(str, Enum):
    NUMERIC = "numeric"
    CODE = "code"
    PROOF = "proof"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"

async def classify_answer_type(query: str) -> AnswerType:
    """Quick LLM call or regex classifier → AnswerType enum."""

async def extract_answer_core(query: str, answer_type: AnswerType) -> str:
    """Strip question framing, return the noun-phrase / concept being asked about.
       E.g. 'What is the time complexity of quicksort?' → 'time complexity of quicksort'"""
```

### 2. `leakage_scorer.py` — Function Signatures

```python
from dataclasses import dataclass

@dataclass
class LeakageScore:
    overall: float         # [0, 1]
    directness: float      # how directly the answer gives the answer
    procedural_reveal: float  # step-by-step solution reveal fraction
    completeness: float    # what fraction of the answer is in the response
    specificity: float     # concreteness of numbers/code/claims

async def compute_leakage(
    query: str,
    response: str,
    chunks: list[dict],
    answer_type: AnswerType,
) -> LeakageScore:
    """Embedding cosine(query_core, response) → directness.
       Structural heuristics per answer_type:
         - NUMERIC: count numerals in response vs. typical
         - CODE: ratio of code-block lines to total
         - PROOF: count of logical-connective tokens (therefore, thus, hence)
         - SHORT_ANSWER: exact-match substring of key terms
         - ESSAY: density of key claims from chunks"""
```

### 3. `differential_redactor.py` — Function Signature

```python
async def redact_response(
    response: str,
    score: LeakageScore,
    answer_type: AnswerType,
    threshold: float = 0.7,
) -> str:
    """Type-aware redaction when score.overall > threshold:
       NUMERIC → replace numbers with placeholders (e.g., [REDACTED_VALUE])
       CODE    → collapse body, keep signature only
       PROOF   → remove final step / conclusion
       SHORT_ANSWER → remove the answer phrase, replace with hint
       ESSAY   → remove key claim sentence identified via embedding similarity
    """
    if score.overall <= threshold:
        return response
    # rule-based, no LLM needed
```

### 4. `integrity_enforcer.py` — Full Class

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
        core, score = await asyncio.gather(
            extract_answer_core(query, atype),
            compute_leakage(query, response, chunks, atype),
        )
        was_redacted = score.overall > settings.LEAKAGE_THRESHOLD
        final = await redact_response(response, score, atype, settings.LEAKAGE_THRESHOLD) if was_redacted else response
        await self._log(query, course_code, atype, score, was_redacted, response, final)
        return final, score, was_redacted

    async def _log(self, query, course_code, atype, score, redacted, original, final):
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
             "lsp": score.specificity, "r": redacted, "o": original, "rf": final if redacted else None},
        )

integrity = IntegrityEnforcer()
```

### 5. Config Additions (`backend/app/config.py`)

After `QUERY_ENHANCER_NUM_QUERIES` (line 69):

```python
INTEGRITY_ENABLED: bool = os.getenv("INTEGRITY_ENABLED", "false").lower() == "true"
LEAKAGE_THRESHOLD: float = float(os.getenv("LEAKAGE_THRESHOLD", "0.7"))
```

### 6. DB Schema (`backend/app/db.py:_init_schema`)

Insert before `DEFINE TABLE IF NOT EXISTS knowledge_state`:

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

### 7. Insertion Points in `backend/app/query_engine.py`

**`query_stream()` — after line 332, before line 333:**

```python
        # ── Stage 8: Integrity & Leakage Enforcement ──
        redacted, leak_score, was_redacted = await integrity.enforce(
            query, full_response, chunks, course_code,
        )
        if was_redacted:
            full_response = redacted
```

**`query()` — after line 413, before line 415:**

```python
        # ── Stage 8: Integrity & Leakage Enforcement ──
        redacted, leak_score, was_redacted = await integrity.enforce(
            query, response_text, chunks, course_code,
        )
        if was_redacted:
            response_text = redacted
```

---

## Phase 2 — Multi-Signal Bloom's Detector

### 1. `bloom_signals.py` — 6 Extractors

```python
import re
from typing import Callable

# Each returns a float in [0, 1] mapped to Bloom level 1-6

async def verb_taxonomy_signal(query: str) -> float:
    """NLTK POS tagging → ratio of Bloom cognitive verbs (define, analyze, design...)
       against total verbs. Maps to level via verb→level lookup table."""

async def syntactic_complexity_signal(query: str) -> float:
    """Clause count (regex on ',' 'and' 'which' 'that') or parse tree depth.
       Longer = higher Bloom."""

async def interrogative_type_signal(query: str) -> float:
    """Regex on question starters: 'what is'→L1, 'explain'→L2, 'how to'→L3,
       'compare'→L4, 'evaluate'→L5, 'design'→L6."""

async def referential_scope_signal(query: str) -> float:
    """NER entity count via spaCy or regex: multi-entity references → higher level."""

async def presupposition_structure_signal(query: str) -> float:
    """Presence of presupposition triggers ('assuming', 'given that', 'suppose') →
       correlates with analysis/evaluation."""

async def predicted_answer_type_signal(query: str) -> float:
    """LLM quick-classify the required answer type → maps to Bloom level.
       Uses a tiny prompt, cached aggressively."""

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

### 2. `bloom_fusion.py`

```python
import numpy as np

# Learned weights: shape (6, 6) — 6 Bloom levels × 6 signals
CALIBRATED_WEIGHTS: np.ndarray = np.array([
    # V  S  I  R  P  A   ← signal indices
    [.4, .1, .3, .05, .05, .1],  # Remember
    [.3, .15, .3, .1, .05, .1],  # Understand
    [.2, .2, .25, .15, .1, .1],  # Apply
    [.1, .2, .15, .25, .2, .1],  # Analyze
    [.05, .15, .1, .2, .3, .2],  # Evaluate
    [.05, .1, .1, .15, .2, .4],  # Create
])

async def fuse_signals(signals: list[float], epsilon: float = 0.05) -> tuple[int, float]:
    """
    signals: [s1..s6] each in [0,1]
    Returns (bloom_level 1-6, confidence in [0,1])
    Weighted sum per level → softmax → highest level with confidence.
    If second-highest is within epsilon of highest, return 0 (uncertain).
    """
    s = np.array(signals)
    scores = CALIBRATED_WEIGHTS @ s
    exp_s = np.exp(scores - np.max(scores))
    probs = exp_s / exp_s.sum()
    ranked = np.argsort(probs)[::-1]
    if len(ranked) >= 2 and (probs[ranked[0]] - probs[ranked[1]]) < epsilon:
        return 0, float(probs[ranked[0]])  # uncertain
    return int(ranked[0]) + 1, float(probs[ranked[0]])
```

### 3. `bloom_verifier.py`

```python
from app.bloom_signals import compute_all_signals
from app.bloom_fusion import fuse_signals

async def verify_bloom_response(
    query: str,
    response: str,
    expected_level: int,
    epsilon: float = 0.05,
) -> tuple[bool, int, float]:
    """Re-run signals on the generated response to verify Bloom alignment.
       Returns (matches, actual_level, confidence)."""
    signals = await compute_all_signals(response)
    actual_level, confidence = await fuse_signals(signals, epsilon)
    return actual_level == expected_level, actual_level, confidence
```

### 4. `bloom_classifier.py` — Refactored

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
        if level != 0:  # confident prediction
            _bloom_cache[question] = level
            return level
        # else fall through to LLM fallback

    # Fallback: existing LLM call (unchanged)
    try:
        response = await client.chat(...)
        ...
    except:
        return None
```

### 5. Config Additions (`backend/app/config.py`)

After `BLOOM_VALIDATION_ENABLED` (line 67):

```python
BLOOM_SIGNALS_ENABLED: bool = os.getenv("BLOOM_SIGNALS_ENABLED", "false").lower() == "true"
BLOOM_EPSILON: float = float(os.getenv("BLOOM_EPSILON", "0.05"))
```

### 6. Insertion in `query_engine.py` (Stage 0, pre-gatekeeper)

**`query_stream()` — after line 247, before line 249:**

```python
        # ── Stage 0: Multi-Signal Bloom's Detector ──
        bloom_level = await self._resolve_bloom_level(query, bloom_level)
```

**`query()` — after line 358, before line 359:**

```python
        bloom_level = await self._resolve_bloom_level(query, bloom_level)
```

**Add helper to `QueryEngine` class:**

```python
    async def _resolve_bloom_level(self, query: str, existing: int | None) -> int | None:
        if existing is not None or not settings.BLOOM_SIGNALS_ENABLED:
            return existing
        return await classify_bloom_level(query)
```

---

## Data Flow Diagram

```
QUERY
  │
  ▼
┌─────────────────────┐
│ Stage 0: Bloom       │ ← bloom_signals → bloom_fusion → bloom_classifier (LLM fallback)
│   Signals Detector   │    bloom_verifier on response (if BLOOM_VALIDATION_ENABLED)
└─────────┬───────────┘
          │ bloom_level
          ▼
┌─────────────────────┐
│ Stage 1: Gatekeeper  │ (unchanged)
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Stage 2-6: Retrieval │ (unchanged)
│ → Context → Strategy │
│ → LLM → Verifier    │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Stage 7: Citation    │ (unchanged)
│   Validation         │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Stage 8: Integrity   │ ← answer_decomposer → leakage_scorer → differential_redactor
│   Enforcement        │    log → integrity_log table
└─────────────────────┘
          │
          ▼
        RESPONSE
```

---

## Latency Risks & Mitigations

| Risk | Phase | Mitigation |
|------|-------|------------|
| 6 sequential signal extractors | P2 | `asyncio.gather(compute_all_signals)` — all 6 parallel (5 rule-based + 1 LLM) |
| `classify_answer_type` + `compute_leakage` each call LLM | P1 | `asyncio.gather(classify, compute)` in `enforce()` |
| NLTK/spaCy model loading | P2 | Lazy-load once at module level |
| `predicted_answer_type_signal` calls LLM | P2 | Cache by query hash; reuse `classify_answer_type` result from P1 |
| Bloom verifier on response | P2 | Only runs when `BLOOM_VALIDATION_ENABLED`; skip if not |

Both phases add **~300ms** on cold path (uncached LLM calls), **~50ms** on hot path (cached signals + rule-based only).

---

## What NOT to Change

| File | Reason |
|------|--------|
| `provider_router.py` | Interface stays stable; no new provider logic needed |
| `gatekeeper.py` | Unchanged — bloom stage feeds *into* gatekeeper, not vice versa |
| `verifier.py` | Phase 1 runs *after* verifier, doesn't modify it |
| `server.py` | No new app state — `query_engine.py` orchestrates internally |
| `routers/query.py` | No API changes; `bloom_level` already passes through |
| existing config keys | Only append `INTEGRITY_*`, `LEAKAGE_*`, `BLOOM_SIGNALS_*`, `BLOOM_EPSILON` |
| `build_tutor_*` / `build_context_window` | Pure functions, stay unchanged |
| `knowledge_state.py` | `BLOOM_LABELS`/`BLOOM_PROMPTS` stay; phase 2 is about *classification* |
| existing tests | Don't touch; add new test file per phase |

---

## Dependencies

- **Python stdlib**: `asyncio`, `dataclasses`, `enum`, `re`
- **NumPy**: for fusion weight matrix (`bloom_fusion.py`)
- **NLTK** (if available): POS tagging for verb taxonomy signal
- **spaCy** (optional): NER for referential scope; regex fallback works
- **Existing**: `provider_router.router.embed_text` for cosine similarity in leakage scorer
