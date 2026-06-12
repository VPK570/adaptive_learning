# Workstreams & Best Practices

## Parallel Workstreams
Define and execute these tracks in parallel:
1. **Security & Privacy**: Auth, input validation, secrets, supply chain.
2. **Reliability & Data Integrity**: Resilience, transactional boundaries, failure modes.
3. **Performance & Scalability**: Efficiency, IO bottlenecks, concurrency.
4. **Observability**: Logs, metrics, traces, health checks.
5. **Maintainability**: CI/CD, testing strategy, developer experience.
6. **Portability & Interop**: Platform independence, API standards.

## Stack-Specific Best Practices
Evaluate material gaps for detected technologies:

- **TypeScript**: `"strict": true`, tsconfig path mappings, `tsc` in CI.
- **Express/Next.js**: Security headers, rate limiting, data-fetching patterns.
- **Python (FastAPI/Django)**: Pydantic validation, `SECURE_*` settings, CSRF, uvicorn timeouts.
- **Go**: Context timeouts, `-race` in CI, module pinning.
- **Docker**: Non-root, multi-stage, pinned digests, seccomp.
- **K8s**: Liveness/readiness, resource requests/limits.
- **Terraform**: Backend state hardening, provider pinning.

## Intent Inference
- Output a concise intent statement: target users, primary use cases, key invariants.
- List misalignments between intent and implementation with [E#].
