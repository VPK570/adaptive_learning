# Lifecycle & Optimization

## E2E Tracing
Trace at least one full path per entrypoint (HTTP/CLI/Job):
- **Flow**: Validation → AuthN/Z → Business Logic → Data Access → IO.
- **Identify**: Logic errors, race risks, state leakage, missed branches.
- **Invariants**: Codify with property-based tests or assertions.

## Journey Validation
- **Happy Paths**: Map user journeys from API/CLI.
- **Gaps**: Identify missing checks, poor UX, or weak observability.
- **Executable**: Provide a test snippet for each journey to ensure it stays "happy."

## Redundancy & Deprecation
### Safe Removal Protocol
1. **Identify**: Reference scans, call-graph sampling, type errors after stubbing.
2. **Guard Tests**: Add tests proving remaining behavior is unaffected.
3. **CI Gate**: Block merges until removal is verified by the pipeline.
4. **Removal**: Mark deprecated → Replace call sites → Soft-delete/Flag → Delete.

## Maintainability & Debt
- **Metrics**: Cyclomatic complexity, fan-in/out, module size outliers.
- **Debt Register**: ROI calculation (Impact vs Effort) for refactors.
- **Sequencing**: Define which refactors gate others (e.g., schema before perf).
