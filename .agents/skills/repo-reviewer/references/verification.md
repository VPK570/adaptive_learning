# Ultra-Deep Verification

## The Verification Bar
- **P0 Items**: Must have direct code evidence + **≥2 independent checks**.
- **P1 Items**: Must have direct code evidence + **≥1 independent check**.
- **P2 Items**: Verified via pattern-based inference or sampling.

## Verification Methods
Use these to confirm findings or disprove assumptions:
1. **Static Analysis**: Semgrep, Bandit, Go Vet, Clippy, ESLint.
2. **Security Scans**: Gitleaks, Trufflehog, OSV-Scanner, Pip-audit.
3. **Dynamic Analysis**: Targeted tests (unit/integration), Fuzzing, Race detectors.
4. **Environment**: CI/Config checks, Container scans (Trivy), Schema dry-runs.
5. **Performance**: Benchmarks, profilers, load tests.

## Disproof Protocol
Before finalizing a recommendation:
1. **Explore Unlikely Perspectives**: Could this be intentional? Is there a hidden guard?
2. **Attempt to Falsify**: Try to prove the "bug" is actually correct behavior.
3. **Triple-Verify**: Use independent methods to cross-reference the claim.
4. **Validate Invariants**: Check pre/postconditions and idempotency.

## Confidence Calibration
- **High**: Verified by runtime/tests + independent static/type analysis.
- **Medium**: Strong static evidence or tests on representative samples.
- **Low**: Pattern-based inference or partial evidence.
