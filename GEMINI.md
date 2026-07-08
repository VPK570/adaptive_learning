# Project Instructions

## Local Skills

The following local skills are installed in `.agents/skills/`:

- **create-skill**: Guide for creating effective skills. To use, manually read `.agents/skills/create-skill/SKILL.md` and its references.
- **repo-reviewer**: Deep, evidence-backed repository auditing for correctness, security, performance, and maintainability. Provides actionable diffs and verification artifacts. To use, manually read `.agents/skills/repo-reviewer/SKILL.md`.

## Critical Findings (from REPOSITORY_AUDIT_REPORT.md)

| Severity | Finding | Location |
|----------|---------|----------|
| 🔴 | Hardcoded OpenRouter API key + JWT secret in docker-compose | `docker-compose.yml:25-26` |
| 🔴 | No auth enforcement on any route | All endpoints |
| 🟠 | Fake token counting (`len(text.split())`) | `chunker.py:6` |
| 🟠 | New HTTPX client per API call (no connection pooling) | `openrouter.py` |
| 🟠 | `except: pass` swallowing errors | `pdf_extractor.py:95-98` |
| 🟠 | No structured logging (all `print()`) | Every backend file |
| 🟠 | Global module-level singletons with no DI | `server.py` |
| 🟡 | Postgres service defined but unused | `docker-compose.yml:46-55` |
| 🟡 | Two frontends with overlapping functionality | `frontend/` + `new_frontend/` |

**Readiness Score: 3.5/10** — early-stage MVP, not production-ready. See the full report at `REPOSITORY_AUDIT_REPORT.md`.

## Development Workflow

- Use `create-skill` when extending the agent's capabilities with new specialized workflows or domain knowledge.
- Use `repo-reviewer` before major changes to audit stability.
- Refer to `docs/API.md` and `docs/ARCHITECTURE.md` for current project state.
- `SPEC.md` contains the original MVP specification (partially outdated).
