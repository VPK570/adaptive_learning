# Report Deliverables

The final review must follow this structure, adjusted for the chosen **verbosity mode**.

### 0) TL;DR
P0/P1 counts, top themes, highest-risk areas, first actions.

### 1) Summary
Assumptions, safety/compliance blockers, and prioritized overview matrix.

### 1a) Best-Practices Compliance Matrix
| Area | Best Practice | Status | Evidence [E#] | Proposed Diff/Verification |
| :--- | :--- | :--- | :--- | :--- |

### 2) Detailed Recommendations
For every P0/P1 recommendation (and sampled P2s):
- **Title & Category**: e.g., "Security: Missing CSRF Protection".
- **Rationale & Evidence [E#]**: Why it matters and where it is in the code.
- **Proposed Change**: Surgical diff/snippet.
- **Impact & Effort**: Expected benefit (SLO) vs H/M/L effort.
- **Risks & Alternatives**: ≥2 options with trade-offs.
- **Verification**: Disproof attempts, artifacts, and one-liner commands.
- **Confidence**: High/Medium/Low.

### 3) E2E Trace Reports
Sequence/call graphs per entrypoint. Must include:
- **Mermaid Sequence Diagram**: Component → function → external deps.
- **Checks**: AuthN/Z, error handling, retries, idempotency, data integrity.

### 4) Journey Validation
Enumerate happy-path user journeys (from routes/API).
- List gaps or brittleness points.
- Provide executable test outlines/snippets per journey.

### 5) Redundancy & Deprecation
Candidates for removal with evidence, guard tests, and CI gating snippets.

### 6) Debt Register
Table with ROI and refactor sequencing (cycles, complexity hotspots).

### 7) Strategic Refactors
>1 day items with roadmaps, migration/rollback plans, and alternative architecture paths.

### 8) Doc Alignment
Mismatches between README/docs and actual implementation with proposed diffs.

### 9) Methods & Limitations
Assumption log, instruction conflicts, and repo snapshot (SHA/versions).
